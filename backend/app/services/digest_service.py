"""Main digest service for generating morning weather digests.

This service orchestrates the digest generation process, including
forecast retrieval, derivation computation, cache management, and
LLM-powered or placeholder narrative generation.
"""

import json
from datetime import date, datetime

import structlog

from app.infrastructure.ai.builders.digest_prompt_builder import create_digest_prompt_builder
from app.infrastructure.ai.llm.azure_client import create_azure_digest_client
from app.infrastructure.cache.digest_cache import (
    digest_cache,
    generate_forecast_signature,
    generate_preferences_hash,
)
from app.core.config import settings
from app.core.exceptions import (
    DigestGenerationError,
    ForecastUnavailableError,
    InvalidDateFormatError,
    UserPreferencesError,
)
from app.infrastructure.db import LLMAuditRepository
from app.infrastructure.observability.digest import digest_instrumentation
from app.schemas.digest import (
    SCHEMA_VERSION,
    CacheMeta,
    Derived,
    DigestResponse,
    TokensMeta,
)
from app.services.digest_placeholder import build_placeholder_summary
from app.services.forecast_derivation import derive_all_metrics
from app.services.llm_client import create_llm_client

logger = structlog.get_logger(__name__)


class DigestService:
    """Service for generating morning weather digests."""

    def __init__(self, forecast_provider, preferences_provider, location_service=None,
                 timezone_resolver=None, llm_audit_repo: LLMAuditRepository = None,
                 use_llm: bool = None):
        """Initialize digest service with dependencies.

        Args:
            forecast_provider: Service for retrieving forecast data
            preferences_provider: Service for retrieving user preferences
            location_service: Service for resolving user locations
            timezone_resolver: Optional timezone resolution service
            llm_audit_repo: Repository for LLM audit logging
            use_llm: Whether to use LLM (True) or placeholder (False).
                    If None, defaults to True when llm_audit_repo is provided.
        """
        self.forecast_provider = forecast_provider
        self.preferences_provider = preferences_provider
        self.location_service = location_service
        self.timezone_resolver = timezone_resolver

        # Determine LLM usage - default to enabled when audit repo is available
        if use_llm is None:
            self.use_llm = llm_audit_repo is not None
        else:
            self.use_llm = use_llm

        # Initialize LLM components if enabled and audit repo available
        if self.use_llm and llm_audit_repo:
            self.llm_client = create_llm_client(llm_audit_repo)
            self.azure_client = create_azure_digest_client(self.llm_client)
            self.prompt_builder = create_digest_prompt_builder()
        else:
            self.llm_client = None
            self.azure_client = None
            self.prompt_builder = None
            if self.use_llm:
                logger.warning(
                    "LLM requested but no audit repository provided, falling back to placeholder",
                    action="digest_service.llm_fallback"
                )

    async def get_morning_digest(self, user_id: str, date: str | None = None,
                               force: bool = False) -> DigestResponse:
        """Generate or retrieve morning digest for user and date.

        This method implements the full digest generation pipeline:
        1. Resolve and validate date
        2. Build cache key from forecast signature and preferences hash
        3. Attempt cache retrieval (unless force=True)
        4. On cache miss: fetch data, derive metrics, generate narrative, cache result
        5. Return digest with cache metadata

        Args:
            user_id: User identifier
            date: Optional date string (YYYY-MM-DD), defaults to today
            force: Force regeneration, bypassing cache

        Returns:
            DigestResponse with generated digest and metadata

        Raises:
            InvalidDateFormatError: If date format is invalid
            ForecastUnavailableError: If forecast data cannot be retrieved
            UserPreferencesError: If user preferences cannot be retrieved
            DigestGenerationError: If digest generation fails
        """
        # Use instrumentation for metrics
        async with digest_instrumentation.measure_digest_generation("morning_digest"):
            logger.info(
                "Starting digest generation",
                action="digest_service.get_morning_digest",
                user_id=user_id,
                date=date,
                force=force
            )

            # Record digest access for daily open rate tracking
            digest_instrumentation.record_digest_access(date)

            # Step 1: Resolve and validate date
            resolved_date = self._resolve_date(date)
            logger.debug("Date resolved", date=resolved_date)

            # Step 2: Get location for user
            location_id = await self._get_user_primary_location(user_id)

            # Step 3: Fetch forecast data and user preferences with preprocessing timing
            async with digest_instrumentation.measure_preprocessing():
                try:
                    forecast_data = await self.forecast_provider.get_forecast(location_id, resolved_date)
                    user_preferences = await self.preferences_provider.get_preferences(user_id)
                except Exception as e:
                    logger.error(
                        "Failed to fetch dependencies",
                        action="digest_service.fetch_dependencies",
                        error=str(e)
                    )
                    if "forecast" in str(e).lower():
                        raise ForecastUnavailableError(f"Forecast data unavailable: {e}") from e
                    else:
                        raise UserPreferencesError(f"User preferences unavailable: {e}") from e

                # Step 4: Generate cache key components
                forecast_sig = generate_forecast_signature(forecast_data)
                prefs_hash = generate_preferences_hash(user_preferences)

                logger.debug(
                    "Cache key components generated",
                    forecast_sig=forecast_sig,
                    prefs_hash=prefs_hash
                )

            # Step 5: Attempt cache retrieval (unless force=True)
            cached_digest = None
            ttl_remaining = None

            if not force:
                try:
                    cached_digest = await digest_cache.get_digest(
                        user_id, resolved_date, forecast_sig, prefs_hash
                    )
                    if cached_digest:
                        ttl_remaining = await digest_cache.get_ttl(
                            user_id, resolved_date, forecast_sig, prefs_hash
                        )
                        digest_instrumentation.record_cache_event("get", hit=True)

                        logger.info(
                            "Cache hit - returning cached digest",
                            action="digest_service.cache_hit",
                            ttl_remaining=ttl_remaining
                        )

                        # Parse cached response and update cache metadata
                        digest_dict = json.loads(cached_digest)
                        digest_dict["cache_meta"]["hit"] = True
                        digest_dict["cache_meta"]["ttl_seconds"] = ttl_remaining

                        return DigestResponse.parse_obj(digest_dict)

                except Exception as e:
                    logger.warning(
                        "Cache retrieval failed, proceeding with generation",
                        action="digest_service.cache_error",
                        error=str(e)
                    )

            # Cache miss - record event
            digest_instrumentation.record_cache_event("get", hit=False)

            # Step 6: Generate new digest
            try:
                digest_response = await self._generate_digest(
                    user_id=user_id,
                    location_id=location_id,
                    date=resolved_date,
                    forecast_data=forecast_data,
                    user_preferences=user_preferences,
                    forecast_sig=forecast_sig,
                    prefs_hash=prefs_hash
                )

                # Step 7: Cache the result
                await self._cache_digest(
                    user_id, resolved_date, forecast_sig, prefs_hash, digest_response
                )

                logger.info(
                    "Digest generation completed",
                    action="digest_service.generation_complete",
                    user_id=user_id,
                    date=resolved_date
                )

                return digest_response

            except Exception as e:
                logger.error(
                    "Digest generation failed",
                    action="digest_service.generation_error",
                    error=str(e)
                )
                raise DigestGenerationError(f"Failed to generate digest: {e}") from e

    def _resolve_date(self, date_str: str | None) -> str:
        """Resolve and validate date string.

        Args:
            date_str: Optional date string (YYYY-MM-DD)

        Returns:
            Validated date string

        Raises:
            InvalidDateFormatError: If date format is invalid
        """
        if date_str is None:
            # Default to today
            return date.today().isoformat()

        # Validate date format
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError as err:
            raise InvalidDateFormatError(f"Invalid date format: {date_str}") from err

    async def _get_user_primary_location(self, user_id: str) -> int:
        """Get user's primary location ID.

        Args:
            user_id: User identifier

        Returns:
            Primary location ID
        """
        if self.location_service:
            try:
                return await self.location_service.get_user_primary_location(user_id)
            except Exception as e:
                logger.warning(
                    "Failed to get user location, using fallback",
                    action="digest_service.location_fallback",
                    user_id=user_id,
                    error=str(e)
                )
                # Fallback to default location
                return 1
        else:
            # Placeholder for when no location service is provided
            return 1

    async def _generate_digest(self, user_id: str, location_id: int, date: str,
                              forecast_data: dict, user_preferences: dict,
                              forecast_sig: str, prefs_hash: str) -> DigestResponse:
        """Generate new digest from forecast data and preferences.

        Args:
            user_id: User identifier
            location_id: Location ID
            date: Date string
            forecast_data: Forecast data dictionary
            user_preferences: User preferences dictionary
            forecast_sig: Forecast signature for cache key
            prefs_hash: Preferences hash for cache key

        Returns:
            Generated DigestResponse
        """
        generation_time = datetime.utcnow()

        # Extract hourly data for derivations
        hourly_data = forecast_data.get("hourly", [])
        if not hourly_data:
            raise ForecastUnavailableError("No hourly forecast data available")

        # Step 1: Derive all metrics
        logger.debug("Computing derived metrics", hourly_count=len(hourly_data))
        derived_data = derive_all_metrics(hourly_data, user_preferences)

        # Step 2: Create Derived object
        derived = Derived(
            temp_min_c=derived_data["temp_min_c"],
            temp_max_c=derived_data["temp_max_c"],
            peak_rain_window=derived_data["peak_rain_window"],
            lowest_wind_window=derived_data["lowest_wind_window"],
            comfort_score=derived_data["comfort_score"],
            activity_blocks=derived_data["activity_blocks"]
        )

        # Step 3: Generate summary (LLM or placeholder) with strict validation
        if self.use_llm and self.azure_client and self.prompt_builder:
            logger.debug("Generating LLM-powered summary")
            async with digest_instrumentation.measure_llm_generation():
                summary, tokens_meta = await self._generate_llm_summary(
                    derived_data=derived_data,
                    user_preferences=user_preferences,
                    date=date,
                    location_id=location_id,
                    user_id=user_id
                )

                # Record token usage for metrics
                if tokens_meta:
                    digest_instrumentation.record_token_usage(
                        tokens_meta.tokens_in,
                        tokens_meta.tokens_out
                    )
        else:
            logger.debug("Generating placeholder summary")
            summary = build_placeholder_summary(derived_data, user_preferences)
            tokens_meta = None

        # Step 4: Strict validation of summary format
        summary = self._validate_and_enforce_summary_format(summary)

        # Step 5: Create cache metadata
        cache_key = digest_cache._generate_cache_key(user_id, date, forecast_sig, prefs_hash)
        cache_meta = CacheMeta(
            hit=False,
            ttl_seconds=settings.digest_cache_ttl_seconds,
            key=cache_key,
            generated_at=generation_time
        )

        # Step 5: Create final response
        return DigestResponse(
            schema_version=SCHEMA_VERSION,
            date=date,
            location_id=location_id,
            user_id=user_id,
            summary=summary,
            derived=derived,
            tokens_meta=tokens_meta,
            cache_meta=cache_meta
        )

    def _validate_and_enforce_summary_format(self, summary):
        """Validate and enforce strict summary format requirements.

        Args:
            summary: Summary object to validate

        Returns:
            Validated and potentially corrected Summary object
        """
        from app.schemas.digest import Bullet, Summary

        # Ensure exactly 3 bullets
        bullets = summary.bullets[:3] if len(summary.bullets) >= 3 else summary.bullets

        # Fill missing bullets if needed
        while len(bullets) < 3:
            bullets.append(Bullet(
                text="Weather conditions require attention - stay informed and plan accordingly",
                category="alert",
                priority=3
            ))

        # Ensure bullets are prioritized (1=high, 2=medium, 3=low)
        for i, bullet in enumerate(bullets):
            if not hasattr(bullet, 'priority') or bullet.priority is None:
                bullets[i].priority = i + 1  # Assign priority based on position

            # Ensure priority is within valid range
            if bullet.priority < 1 or bullet.priority > 3:
                bullets[i].priority = min(3, max(1, bullet.priority))

        # Sort bullets by priority (1=highest priority first)
        bullets.sort(key=lambda b: b.priority)

        # Trim bullet text to reasonable length (max 150 chars per bullet)
        for i, bullet in enumerate(bullets):
            if len(bullet.text) > 150:
                bullets[i].text = bullet.text[:147] + "..."

        # Trim narrative to reasonable length (max 300 chars)
        narrative = summary.narrative
        if len(narrative) > 300:
            narrative = narrative[:297] + "..."

        # Ensure driver is present and reasonable length
        driver = summary.driver
        if not driver or len(driver.strip()) == 0:
            driver = "Weather conditions are the primary factor for today's planning"
        elif len(driver) > 200:
            driver = driver[:197] + "..."

        return Summary(
            narrative=narrative,
            bullets=bullets,
            driver=driver
        )

    async def _cache_digest(self, user_id: str, date: str, forecast_sig: str,
                           prefs_hash: str, digest_response: DigestResponse) -> None:
        """Cache the generated digest.

        Args:
            user_id: User identifier
            date: Date string
            forecast_sig: Forecast signature
            prefs_hash: Preferences hash
            digest_response: Generated digest response
        """
        try:
            digest_json = digest_response.json()
            await digest_cache.set_digest(
                user_id=user_id,
                date=date,
                forecast_sig=forecast_sig,
                prefs_hash=prefs_hash,
                digest_json=digest_json,
                ttl_seconds=settings.digest_cache_ttl_seconds
            )

            logger.debug(
                "Digest cached successfully",
                action="digest_service.cache_set",
                ttl_seconds=settings.digest_cache_ttl_seconds
            )

        except Exception as e:
            # Log but don't fail the request
            logger.warning(
                "Failed to cache digest",
                action="digest_service.cache_set_error",
                error=str(e)
            )

    async def _generate_llm_summary(
        self,
        derived_data: dict,
        user_preferences: dict,
        date: str,
        location_id: int,
        user_id: str
    ) -> tuple:
        """Generate summary using LLM with strict token budget and validation.

        Args:
            derived_data: Derived weather metrics
            user_preferences: User preferences
            date: Date string
            location_id: Location ID
            user_id: User ID

        Returns:
            Tuple of (Summary object, TokensMeta object)

        Raises:
            DigestGenerationError: If LLM generation fails critically
        """
        try:
            # Build the prompt with context
            location_name = f"Location {location_id}"  # In real impl, resolve from DB
            prompt = self.prompt_builder.build_prompt(
                date=date,
                location_name=location_name,
                user_preferences=user_preferences,
                derived_metrics=derived_data
            )

            # Enforce token budget - estimate input tokens and adjust if needed
            estimated_input_tokens = self._estimate_token_count(prompt)
            max_input_tokens = 120  # Reserve most budget for output
            max_output_tokens = 180  # As specified in issue requirements

            if estimated_input_tokens > max_input_tokens:
                logger.warning(
                    "Input prompt exceeds token budget, trimming",
                    action="digest_service.token_budget_exceeded",
                    estimated_tokens=estimated_input_tokens,
                    max_tokens=max_input_tokens
                )
                prompt = self._trim_prompt_to_budget(prompt, max_input_tokens)

            # Generate with Azure client with explicit token limits
            context = self.prompt_builder.build_context(
                date=date,
                location_name=location_name,
                user_preferences=user_preferences,
                derived_metrics=derived_data
            )

            llm_result = await self.azure_client.generate_digest_summary(
                context=context,
                prompt=prompt,
                user_id=int(user_id) if user_id.isdigit() else None,
                location_id=location_id,
                max_tokens=max_output_tokens
            )

            # Validate token budget compliance
            if llm_result.tokens_out > max_output_tokens:
                logger.warning(
                    "LLM output exceeded token budget",
                    action="digest_service.output_budget_exceeded",
                    actual_tokens=llm_result.tokens_out,
                    max_tokens=max_output_tokens
                )

            # Parse and validate the LLM response JSON
            import json

            from app.schemas.digest import Bullet, Summary

            try:
                response_data = json.loads(llm_result.content)
            except json.JSONDecodeError as e:
                logger.error(
                    "LLM returned invalid JSON, falling back to placeholder",
                    action="digest_service.invalid_json",
                    error=str(e),
                    content_preview=llm_result.content[:200]
                )
                return self._fallback_to_placeholder(derived_data, user_preferences)

            # Validate required fields exist
            if not all(key in response_data for key in ["narrative", "bullets", "driver"]):
                logger.error(
                    "LLM response missing required fields, falling back to placeholder",
                    action="digest_service.missing_fields",
                    fields_present=list(response_data.keys())
                )
                return self._fallback_to_placeholder(derived_data, user_preferences)

            # Create Summary object from LLM response with validation
            try:
                bullets = [
                    Bullet(
                        text=bullet.get("text", "").strip(),
                        category=bullet.get("category", "alert"),
                        priority=bullet.get("priority", 2)
                    )
                    for bullet in response_data["bullets"]
                    if bullet.get("text", "").strip()  # Skip empty bullets
                ]

                # Ensure we have exactly 3 valid bullets
                if len(bullets) < 3:
                    logger.warning(
                        "LLM provided insufficient bullets, padding with defaults",
                        action="digest_service.insufficient_bullets",
                        bullet_count=len(bullets)
                    )

                summary = Summary(
                    narrative=response_data["narrative"].strip(),
                    bullets=bullets,
                    driver=response_data["driver"].strip()
                )

            except (KeyError, TypeError, ValueError) as e:
                logger.error(
                    "Failed to parse LLM response format, falling back to placeholder",
                    action="digest_service.parse_error",
                    error=str(e)
                )
                return self._fallback_to_placeholder(derived_data, user_preferences)

            # Create TokensMeta
            tokens_meta = TokensMeta(
                tokens_in=llm_result.tokens_in,
                tokens_out=llm_result.tokens_out,
                model=llm_result.model,
                cost_usd=llm_result.cost_usd
            )

            logger.info(
                "LLM summary generated successfully",
                action="digest_service.llm_success",
                tokens_in=llm_result.tokens_in,
                tokens_out=llm_result.tokens_out,
                cost_usd=llm_result.cost_usd,
                duration_ms=llm_result.duration_ms,
                within_budget=llm_result.tokens_out <= max_output_tokens
            )

            return summary, tokens_meta

        except Exception as e:
            logger.error(
                "LLM summary generation failed, falling back to placeholder",
                action="digest_service.llm_error",
                error=str(e)
            )
            return self._fallback_to_placeholder(derived_data, user_preferences)

    def _fallback_to_placeholder(self, derived_data: dict, user_preferences: dict) -> tuple:
        """Generate fallback placeholder summary when LLM fails.

        Args:
            derived_data: Derived weather metrics
            user_preferences: User preferences

        Returns:
            Tuple of (Summary object, TokensMeta object)
        """
        summary = build_placeholder_summary(derived_data, user_preferences)
        tokens_meta = TokensMeta(
            tokens_in=0,
            tokens_out=0,
            model="placeholder-fallback",
            cost_usd=0.0
        )
        return summary, tokens_meta

    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count for given text.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count (rough approximation)
        """
        # Rough estimation: ~4 characters per token on average
        return len(text) // 4

    def _trim_prompt_to_budget(self, prompt: str, max_tokens: int) -> str:
        """Trim prompt to fit within token budget.

        Args:
            prompt: Original prompt text
            max_tokens: Maximum allowed tokens

        Returns:
            Trimmed prompt text
        """
        max_chars = max_tokens * 4  # Rough estimation
        if len(prompt) <= max_chars:
            return prompt

        # Trim from the middle to preserve structure
        return prompt[:max_chars//2] + "...[trimmed]..." + prompt[-max_chars//2:]
