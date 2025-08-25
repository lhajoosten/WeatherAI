"""Main digest service for generating morning weather digests.

This service orchestrates the digest generation process, including
forecast retrieval, derivation computation, cache management, and
placeholder narrative generation for PR1.
"""

import json
from datetime import datetime, date
from typing import Optional, Dict, Any

import structlog

from app.schemas.digest import DigestResponse, Derived, CacheMeta, SCHEMA_VERSION
from app.services.forecast_derivation import derive_all_metrics
from app.services.digest_placeholder import build_placeholder_summary
from app.cache.digest_cache import (
    digest_cache, 
    generate_forecast_signature, 
    generate_preferences_hash
)
from app.metrics.digest import digest_instrumentation
from app.core.config import settings
from app.core.exceptions import (
    ForecastUnavailableError, 
    InvalidDateFormatError, 
    UserPreferencesError,
    DigestGenerationError
)

logger = structlog.get_logger(__name__)


class DigestService:
    """Service for generating morning weather digests."""
    
    def __init__(self, forecast_provider, preferences_provider, timezone_resolver=None):
        """Initialize digest service with dependencies.
        
        Args:
            forecast_provider: Service for retrieving forecast data
            preferences_provider: Service for retrieving user preferences
            timezone_resolver: Optional timezone resolution service
        """
        self.forecast_provider = forecast_provider
        self.preferences_provider = preferences_provider
        self.timezone_resolver = timezone_resolver
        
    async def get_morning_digest(self, user_id: str, date: Optional[str] = None, 
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
            
            # Step 1: Resolve and validate date
            resolved_date = self._resolve_date(date)
            logger.debug("Date resolved", date=resolved_date)
            
            # Step 2: Get location for user (assuming primary location for now)
            # Note: In a real implementation, this would get the user's primary location
            # For PR1, we'll use a placeholder location_id
            location_id = await self._get_user_primary_location(user_id)
            
            # Step 3: Fetch forecast data and user preferences
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
                    raise ForecastUnavailableError(f"Forecast data unavailable: {e}")
                else:
                    raise UserPreferencesError(f"User preferences unavailable: {e}")
            
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
            cache_hit = False
            ttl_remaining = None
            
            if not force:
                try:
                    cached_digest = await digest_cache.get_digest(
                        user_id, resolved_date, forecast_sig, prefs_hash
                    )
                    if cached_digest:
                        cache_hit = True
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
                raise DigestGenerationError(f"Failed to generate digest: {e}")
    
    def _resolve_date(self, date_str: Optional[str]) -> str:
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
        except ValueError:
            raise InvalidDateFormatError(f"Invalid date format: {date_str}")
    
    async def _get_user_primary_location(self, user_id: str) -> int:
        """Get user's primary location ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            Primary location ID
            
        Note:
            In PR1, this returns a placeholder. In a real implementation,
            this would query the user's preferences or default location.
        """
        # Placeholder for PR1 - would query user's primary location
        return 1
    
    async def _generate_digest(self, user_id: str, location_id: int, date: str,
                              forecast_data: Dict, user_preferences: Dict,
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
        
        # Step 3: Generate placeholder summary
        logger.debug("Generating placeholder summary")
        summary = build_placeholder_summary(derived_data, user_preferences)
        
        # Step 4: Create cache metadata
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
            tokens_meta=None,  # None in PR1
            cache_meta=cache_meta
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