"""Use cases for weather-related operations.

This module contains application use cases that orchestrate domain
and infrastructure components for weather functionality.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.application.event_bus import get_event_bus
from app.domain.events import WeatherExplanationGeneratedEvent, DigestGeneratedEvent
from app.domain.exceptions import NotFoundError, ValidationError
from app.infrastructure.db.models import Location

logger = logging.getLogger(__name__)

# Prompt version constant for tracking
EXPLAIN_PROMPT_VERSION = "explain_v2"
DIGEST_PROMPT_VERSION = "digest_v1"


class ExplainWeatherUseCase:
    """Use case for generating weather explanations using structured facts."""

    def __init__(
        self,
        llm_client,  # Infrastructure dependency
        forecast_repository,  # Infrastructure dependency
    ):
        self.llm_client = llm_client
        self.forecast_repo = forecast_repository
        self.event_bus = get_event_bus()

    async def execute(self, location: Location, user_id: int) -> dict[str, Any]:
        """Generate weather explanation for a location using structured facts.

        Args:
            location: Location to explain weather for
            user_id: User ID for audit logging

        Returns:
            Dict with summary, actions, driver, and token metadata

        Raises:
            NotFoundError: If location data is not available
            ValidationError: If input parameters are invalid
        """
        if not location:
            raise ValidationError("Location is required")

        if not user_id:
            raise ValidationError("User ID is required")

        logger.info(f"Generating weather explanation for location {location.id}")

        # Get cached forecast data
        forecast_cache = await self.forecast_repo.get_latest_for_location(location.id)

        if not forecast_cache:
            # Create mock forecast data for demo
            logger.info("No cached forecast found, creating mock data")
            await self._create_mock_forecast(location.id)
            forecast_cache = await self.forecast_repo.get_latest_for_location(location.id)

        if not forecast_cache:
            raise NotFoundError(f"No forecast data available for location {location.id}")

        # Build structured facts from forecast data
        structured_facts = self._build_structured_facts(location, forecast_cache)

        # Generate prompt using template
        prompt = self._build_explain_prompt(structured_facts)

        # Call LLM with updated prompt version metadata
        llm_response = await self.llm_client.generate(
            prompt=prompt,
            user_id=user_id,
            endpoint="explain",
            temperature=0.1,  # Low temperature for factual responses
            max_tokens=400,
            prompt_version=EXPLAIN_PROMPT_VERSION,
            location_id=location.id
        )

        # Parse response into structured format
        parsed_response = self._parse_explain_response(llm_response["text"])

        # Publish domain event
        event = WeatherExplanationGeneratedEvent(
            user_id=user_id,
            location_id=location.id,
            explanation_type="weather",
            tokens_used=llm_response["tokens_in"] + llm_response["tokens_out"]
        )
        await self.event_bus.publish(event)

        return {
            "summary": parsed_response["summary"],
            "actions": parsed_response["actions"],
            "driver": parsed_response["driver"],
            "tokens_in": llm_response["tokens_in"],
            "tokens_out": llm_response["tokens_out"],
            "model": llm_response["model"]
        }

    def _get_derived_location_metadata(self, location: Location) -> dict[str, Any]:
        """Calculate derived metadata for location differentiation."""
        lat = location.lat

        # Hemisphere calculation
        hemisphere = "northern" if lat >= 0 else "southern"

        # Latitude band calculation
        abs_lat = abs(lat)
        if abs_lat < 23.5:
            lat_band = "tropical"
        elif abs_lat < 55:
            lat_band = "temperate"
        else:
            lat_band = "polar"

        # Local datetime calculation (simplified - using timezone or UTC)
        try:
            if location.timezone:
                tz = ZoneInfo(location.timezone)
                local_time = datetime.now(tz)
            else:
                local_time = datetime.utcnow()
        except Exception:
            # Fallback to UTC if timezone parsing fails
            local_time = datetime.utcnow()

        time_period = self._determine_time_period(local_time)

        return {
            "hemisphere": hemisphere,
            "latitude_band": lat_band,
            "local_time": local_time.strftime("%Y-%m-%d %H:%M"),
            "time_period": time_period
        }

    def _determine_time_period(self, local_time: datetime) -> str:
        """Determine time period based on local hour."""
        hour = local_time.hour
        if 5 <= hour < 11:
            return "morning"
        elif 11 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    def _build_structured_facts(self, location: Location, forecast_cache) -> dict[str, Any]:
        """Build structured facts from location and forecast data."""
        facts = {
            "location": {
                "name": location.name,
                "country": location.country,
                "lat": location.lat,
                "lon": location.lon,
            },
            "metadata": self._get_derived_location_metadata(location),
            "current": {},
            "forecast": {}
        }

        # Parse forecast data if available
        if forecast_cache and forecast_cache.data:
            forecast_data = forecast_cache.data
            
            # Add current conditions
            if "current" in forecast_data:
                current = forecast_data["current"]
                facts["current"] = {
                    "temperature": current.get("temperature_2m"),
                    "humidity": current.get("relative_humidity_2m"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "wind_direction": current.get("wind_direction_10m"),
                    "weather_code": current.get("weather_code"),
                    "is_day": current.get("is_day")
                }

            # Add forecast data (next 24-48 hours)
            if "hourly" in forecast_data:
                hourly = forecast_data["hourly"]
                facts["forecast"] = {
                    "next_24h_temps": hourly.get("temperature_2m", [])[:24],
                    "next_24h_precipitation": hourly.get("precipitation", [])[:24],
                    "next_24h_wind": hourly.get("wind_speed_10m", [])[:24]
                }

        return facts

    def _build_explain_prompt(self, facts: dict[str, Any]) -> str:
        """Build the explanation prompt using structured facts."""
        facts_json = json.dumps(facts, indent=2)
        
        prompt = f"""System: You are a concise weather assistant. Use only the Data section. Do not invent values.

Data: {facts_json}

Task: Analyze the weather data and produce:
1. A 2-3 sentence summary of current conditions and what to expect
2. 3 short, actionable items for the day
3. A brief explanation of the main weather driver

Format your response as:
Summary: [your summary]

Actions:
- [action 1]
- [action 2] 
- [action 3]

Driver: [main weather driver explanation]

Keep responses practical and location-appropriate."""

        return prompt

    def _parse_explain_response(self, response_text: str) -> dict[str, Any]:
        """Parse LLM response into structured format."""
        lines = response_text.strip().split('\n')
        
        summary = ""
        actions = []
        driver = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Summary:"):
                current_section = "summary"
                summary = line.replace("Summary:", "").strip()
            elif line.startswith("Actions:"):
                current_section = "actions"
            elif line.startswith("Driver:"):
                current_section = "driver"
                driver = line.replace("Driver:", "").strip()
            elif line.startswith("- "):
                if current_section == "actions":
                    actions.append(line.replace("- ", "").strip())
            elif current_section == "summary" and summary:
                summary += " " + line
            elif current_section == "driver" and driver:
                driver += " " + line

        return {
            "summary": summary or "Weather information available.",
            "actions": actions or ["Check weather updates", "Plan accordingly", "Stay informed"],
            "driver": driver or "Standard weather patterns"
        }

    async def _create_mock_forecast(self, location_id: int):
        """Create mock forecast data for demonstration purposes."""
        mock_data = {
            "current": {
                "temperature_2m": 22.5,
                "relative_humidity_2m": 65,
                "wind_speed_10m": 8.2,
                "wind_direction_10m": 245,
                "weather_code": 3,
                "is_day": 1
            },
            "hourly": {
                "temperature_2m": [22.5, 21.8, 20.2, 19.5] + [18.0] * 20,
                "precipitation": [0.0, 0.1, 0.3, 0.0] + [0.0] * 20,
                "wind_speed_10m": [8.2, 7.5, 6.8, 6.2] + [5.5] * 20
            }
        }

        # Store mock data - simplified for demo
        try:
            await self.forecast_repo.store_forecast_data(location_id, mock_data)
        except Exception as e:
            logger.warning(f"Could not store mock forecast data: {e}")


class GenerateDigestUseCase:
    """Use case for generating morning weather digests."""

    def __init__(
        self,
        forecast_provider,  # Infrastructure dependency
        preferences_provider,  # Infrastructure dependency
        location_service,  # Infrastructure dependency
        llm_client,  # Infrastructure dependency
        cache_service,  # Infrastructure dependency
    ):
        self.forecast_provider = forecast_provider
        self.preferences_provider = preferences_provider
        self.location_service = location_service
        self.llm_client = llm_client
        self.cache_service = cache_service
        self.event_bus = get_event_bus()

    async def execute(
        self, 
        user_id: str, 
        date_str: str | None = None, 
        force: bool = False
    ) -> dict[str, Any]:
        """Generate or retrieve morning digest for user and date.

        Args:
            user_id: User identifier
            date_str: Optional date string (YYYY-MM-DD), defaults to today
            force: Force regeneration, bypassing cache

        Returns:
            Dict with digest content and metadata

        Raises:
            ValidationError: If input parameters are invalid
            NotFoundError: If user or location data is not available
        """
        if not user_id:
            raise ValidationError("User ID is required")

        logger.info(f"Generating digest for user {user_id}, date: {date_str}")

        # Resolve date
        target_date = self._resolve_date(date_str)

        # Get user's primary location
        location_id = await self._get_user_primary_location(user_id)
        if not location_id:
            raise NotFoundError(f"No primary location found for user {user_id}")

        # Check cache first (unless force regeneration)
        cache_key = f"digest:{user_id}:{target_date}"
        if not force:
            cached_digest = await self.cache_service.get(cache_key)
            if cached_digest:
                logger.info("Returning cached digest")
                return cached_digest

        # Fetch forecast data and user preferences
        try:
            forecast_data = await self.forecast_provider.get_forecast(location_id, target_date)
            user_preferences = await self.preferences_provider.get_preferences(user_id)
        except Exception as e:
            logger.error(f"Failed to fetch dependencies: {e}")
            raise NotFoundError(f"Could not retrieve required data: {e}")

        # Generate digest
        digest_content = await self._generate_digest_content(
            user_id, location_id, target_date, forecast_data, user_preferences
        )

        # Cache the result
        await self.cache_service.set(cache_key, digest_content, ttl=3600)  # 1 hour TTL

        # Publish domain event
        event = DigestGeneratedEvent(
            user_id=user_id,
            location_id=str(location_id),
            digest_type="morning"
        )
        await self.event_bus.publish(event)

        return digest_content

    def _resolve_date(self, date_str: str | None) -> str:
        """Resolve date string to YYYY-MM-DD format."""
        if date_str is None:
            return datetime.now().strftime("%Y-%m-%d")
        
        # Validate date format
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            raise ValidationError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")

    async def _get_user_primary_location(self, user_id: str) -> int | None:
        """Get user's primary location ID."""
        try:
            location = await self.location_service.get_primary_location(user_id)
            return location.id if location else None
        except Exception as e:
            logger.error(f"Failed to get primary location for user {user_id}: {e}")
            return None

    async def _generate_digest_content(
        self,
        user_id: str,
        location_id: int,
        date: str,
        forecast_data: dict,
        user_preferences: dict
    ) -> dict[str, Any]:
        """Generate digest content using LLM."""
        # Build structured prompt
        prompt = self._build_digest_prompt(forecast_data, user_preferences, date)

        # Call LLM
        llm_response = await self.llm_client.generate(
            prompt=prompt,
            user_id=user_id,
            endpoint="digest",
            temperature=0.2,
            max_tokens=500,
            prompt_version=DIGEST_PROMPT_VERSION,
            location_id=location_id
        )

        # Parse and structure response
        digest_content = self._parse_digest_response(llm_response["text"])

        return {
            "summary": digest_content["summary"],
            "recommendations": digest_content["recommendations"],
            "highlights": digest_content["highlights"],
            "date": date,
            "location_id": location_id,
            "tokens_in": llm_response["tokens_in"],
            "tokens_out": llm_response["tokens_out"],
            "model": llm_response["model"],
            "generated_at": datetime.now().isoformat()
        }

    def _build_digest_prompt(self, forecast_data: dict, user_preferences: dict, date: str) -> str:
        """Build digest generation prompt."""
        forecast_json = json.dumps(forecast_data, indent=2)
        preferences_json = json.dumps(user_preferences, indent=2)

        prompt = f"""System: You are a morning weather assistant. Generate a personalized weather digest for {date}.

Forecast Data: {forecast_json}

User Preferences: {preferences_json}

Task: Create a morning weather digest with:
1. A brief, friendly summary of the day's weather
2. 3-4 personalized recommendations based on preferences
3. 2-3 key weather highlights to watch for

Format your response as:
Summary: [friendly morning weather summary]

Recommendations:
- [personalized recommendation 1]
- [personalized recommendation 2]
- [personalized recommendation 3]

Highlights:
- [key highlight 1]
- [key highlight 2]

Keep the tone conversational and helpful."""

        return prompt

    def _parse_digest_response(self, response_text: str) -> dict[str, Any]:
        """Parse LLM response into structured digest format."""
        lines = response_text.strip().split('\n')
        
        summary = ""
        recommendations = []
        highlights = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Summary:"):
                current_section = "summary"
                summary = line.replace("Summary:", "").strip()
            elif line.startswith("Recommendations:"):
                current_section = "recommendations"
            elif line.startswith("Highlights:"):
                current_section = "highlights"
            elif line.startswith("- "):
                item = line.replace("- ", "").strip()
                if current_section == "recommendations":
                    recommendations.append(item)
                elif current_section == "highlights":
                    highlights.append(item)
            elif current_section == "summary" and summary:
                summary += " " + line

        return {
            "summary": summary or "Weather information for today.",
            "recommendations": recommendations or ["Check weather updates", "Plan accordingly"],
            "highlights": highlights or ["Standard weather conditions"]
        }