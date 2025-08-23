import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.db.models import Location
from app.db.repositories import ForecastRepository
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

# Prompt version constant for tracking
EXPLAIN_PROMPT_VERSION = "explain_v2"


class ExplainService:
    """Service for generating weather explanations using structured facts."""

    def __init__(self, llm_client: LLMClient, forecast_repo: ForecastRepository):
        self.llm_client = llm_client
        self.forecast_repo = forecast_repo

    async def explain_location_weather(self, location: Location, user_id: int) -> dict[str, Any]:
        """Generate weather explanation for a location using structured facts.
        
        Args:
            location: Location to explain weather for
            user_id: User ID for audit logging
            
        Returns:
            Dict with summary, actions, driver, and token metadata
        """
        logger.info(f"Generating weather explanation for location {location.id}")

        # Get cached forecast data
        forecast_cache = await self.forecast_repo.get_latest_for_location(location.id)

        if not forecast_cache:
            # Create mock forecast data for demo
            logger.info("No cached forecast found, creating mock data")
            await self._create_mock_forecast(location.id)
            forecast_cache = await self.forecast_repo.get_latest_for_location(location.id)

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
            
        local_datetime_now = local_time.strftime("%Y-%m-%d %H:%M")
        
        # Daylight flag calculation (naive: 7-19 local hour)
        local_hour = local_time.hour
        daylight_flag = 7 <= local_hour <= 19
        
        return {
            "hemisphere": hemisphere,
            "lat_band": lat_band,
            "local_datetime_now": local_datetime_now,
            "daylight_flag": daylight_flag
        }

    def _build_structured_facts(self, location: Location, forecast_cache) -> dict[str, Any]:
        """Build structured facts from forecast data to prevent hallucination."""
        if not forecast_cache:
            return {
                "location": {
                    "name": location.name,
                    "lat": location.lat,
                    "lon": location.lon,
                    "timezone": location.timezone or "UTC"
                },
                "error": "No forecast data available"
            }

        try:
            forecast_data = json.loads(forecast_cache.payload_json)
        except json.JSONDecodeError:
            forecast_data = {"error": "Invalid forecast data"}

        # Add derived fields for location differentiation (explain_v2)
        derived_fields = self._get_derived_location_metadata(location)

        return {
            "location": {
                "name": location.name,
                "lat": location.lat,
                "lon": location.lon,
                "timezone": location.timezone or "UTC",
                **derived_fields
            },
            "forecast": forecast_data,
            "data_source": forecast_cache.source,
            "fetched_at": forecast_cache.fetched_at.isoformat(),
            "expires_at": forecast_cache.expires_at.isoformat()
        }

    def _build_explain_prompt(self, structured_facts: dict[str, Any]) -> str:
        """Build prompt using explain_v2 template with guardrails."""
        facts_json = json.dumps(structured_facts, indent=2)

        return f"""System: You are a concise weather assistant. Use ONLY the data provided in the Data section below. Do not invent, estimate, or hallucinate any weather measurements, temperatures, or conditions not explicitly provided.

Data:
{facts_json}

Task: Based ONLY on the provided data, produce:
1. A 2-3 sentence summary of the weather conditions considering the location context (hemisphere, latitude band, local time, daylight)
2. Exactly 3 practical action items (bullet points) appropriate for the location and time
3. A brief explanation of the main weather driver/pattern considering geographic context

Format your response as:
Summary: [your summary here]

Actions:
- [action 1]
- [action 2]  
- [action 3]

Driver: [main weather driver explanation]

If any required data is missing or unclear, state "Information unavailable" for that section rather than guessing."""

    def _parse_explain_response(self, response_text: str) -> dict[str, Any]:
        """Parse LLM response into structured components with fallback."""
        try:
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
                    summary = line[8:].strip()
                elif line.startswith("Actions:"):
                    current_section = "actions"
                elif line.startswith("Driver:"):
                    current_section = "driver"
                    driver = line[7:].strip()
                elif line.startswith("- ") and current_section == "actions":
                    actions.append(line[2:].strip())
                elif current_section == "summary" and summary:
                    summary += " " + line
                elif current_section == "driver" and driver:
                    driver += " " + line

            # Ensure we have at least something
            if not summary:
                summary = "Weather information processed successfully."
            if not actions:
                actions = ["Check weather updates regularly", "Plan accordingly", "Stay informed"]
            if not driver:
                driver = "Standard weather patterns observed."

            return {
                "summary": summary,
                "actions": actions[:3],  # Limit to 3 actions
                "driver": driver
            }

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "summary": "Weather analysis completed.",
                "actions": ["Check current conditions", "Monitor for updates", "Plan outdoor activities accordingly"],
                "driver": "Unable to parse detailed weather analysis."
            }

    async def _create_mock_forecast(self, location_id: int):
        """Create mock forecast data for demo purposes with location-based variation."""
        # Get location to calculate variation
        from sqlalchemy import select
        result = await self.forecast_repo.session.execute(
            select(Location).where(Location.id == location_id)
        )
        location = result.scalar_one_or_none()
        if not location:
            logger.error(f"Location {location_id} not found for mock forecast")
            return
            
        # Create deterministic variation based on location
        variation_seed = self._get_location_variation_seed(location_id, location.lat, location.lon)
        
        # Apply variation to base weather values
        base_temp = 22.5 + variation_seed * 8  # Vary between ~14.5 and 30.5°C
        base_humidity = max(30, min(85, 65 + variation_seed * 20))  # 30-85%
        base_wind = max(2, 8.5 + variation_seed * 6)  # 2-14.5 kph
        
        # Different conditions based on variation
        conditions_list = ["sunny", "partly cloudy", "cloudy", "overcast", "light rain"]
        condition_idx = int(abs(variation_seed) * len(conditions_list)) % len(conditions_list)
        base_condition = conditions_list[condition_idx]
        
        mock_forecast = {
            "current": {
                "temperature": round(base_temp, 1),
                "humidity": int(base_humidity),
                "wind_speed": round(base_wind, 1),
                "wind_direction": "SW" if variation_seed > 0 else "NE",
                "conditions": base_condition,
                "visibility": max(5, 10 + variation_seed * 5)
            },
            "hourly_48h": [
                {
                    "time": (datetime.utcnow() + timedelta(hours=i)).isoformat(),
                    "temperature": round(base_temp - (i * 0.2) + variation_seed, 1),
                    "precipitation_probability": max(0, min(80, int(20 + i * 2 + variation_seed * 10))),
                    "wind_speed": round(base_wind + (i * 0.1), 1),
                    "conditions": base_condition if i < 12 else "cloudy"
                }
                for i in range(48)
            ],
            "daily_7d": [
                {
                    "date": (datetime.utcnow() + timedelta(days=i)).date().isoformat(),
                    "temp_high": round(base_temp + 3 - i * 0.5, 1),
                    "temp_low": round(base_temp - 5 - i * 0.3, 1),
                    "precipitation_probability": max(0, min(80, int(20 + i * 5 + variation_seed * 8))),
                    "conditions": base_condition
                }
                for i in range(7)
            ]
        }

        expires_at = datetime.utcnow() + timedelta(hours=6)

        await self.forecast_repo.create(
            location_id=location_id,
            source="mock",
            payload_json=json.dumps(mock_forecast),
            expires_at=expires_at
        )

    def _get_location_variation_seed(self, location_id: int, lat: float, lon: float) -> float:
        """Generate deterministic variation seed based on location coordinates."""
        # Create stable hash of location data for consistent variation
        location_string = f"{location_id}:{round(lat, 2)}:{round(lon, 2)}"
        hash_obj = hashlib.md5(location_string.encode())
        hash_int = int(hash_obj.hexdigest()[:8], 16)
        
        # Convert to float between -1 and 1
        return (hash_int % 20001 - 10000) / 10000.0
