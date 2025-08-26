"""OpenMeteo observation provider implementation."""
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.settings import settings
from app.core.datetime_utils import parse_iso_utc
from app.infrastructure.ingestion.providers import ObservationProvider

logger = logging.getLogger(__name__)


class OpenMeteoObservationProvider(ObservationProvider):
    """OpenMeteo observation provider using free historical API."""

    def __init__(self):
        self.base_url = settings.openmeteo_base_url
        self.timeout = 30.0

    @property
    def provider_name(self) -> str:
        return "openmeteo"

    async def fetch_observations(self, location_id: int, lat: float, lon: float, hours_back: int = 24) -> list[dict[str, Any]]:
        """Fetch observation data from OpenMeteo historical API."""
        logger.info(f"Fetching OpenMeteo observations for location {location_id} at {lat}, {lon} ({hours_back} hours back)")

        # Calculate date range (OpenMeteo historical requires date range)
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(hours=hours_back)

        # Format dates for API (YYYY-MM-DD)
        start_date.strftime("%Y-%m-%d")
        end_date.strftime("%Y-%m-%d")

        # OpenMeteo historical endpoint
        url = f"{self.base_url}/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,wind_speed_10m,relative_humidity_2m,precipitation",
            "past_days": min(7, max(1, hours_back // 24 + 1)),  # Limit to max 7 days past data
            "forecast_days": 0,  # No forecast, only past data
            "timezone": "UTC"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                return self._normalize_observation_data(location_id, data, hours_back)

            except httpx.RequestError as e:
                logger.error(f"Network error fetching OpenMeteo observations for location {location_id}: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching OpenMeteo observations for location {location_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching OpenMeteo observations for location {location_id}: {e}")
                raise

    def _normalize_observation_data(self, location_id: int, data: dict[str, Any], hours_back: int) -> list[dict[str, Any]]:
        """Normalize OpenMeteo observation response to our standard format."""
        hourly = data.get("hourly", {})

        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        wind_speeds = hourly.get("wind_speed_10m", [])
        humidity = hourly.get("relative_humidity_2m", [])
        precipitation = hourly.get("precipitation", [])

        # Filter to only include data within our requested time range
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours_back)

        records = []
        for i, time_str in enumerate(times):
            try:
                # Use centralized datetime parsing for consistency
                observed_at = parse_iso_utc(time_str)

                # Skip if outside our time range or future data
                if observed_at < cutoff_time or observed_at > datetime.now(UTC):
                    continue

                record = {
                    "location_id": location_id,
                    "observed_at": observed_at,
                    "temp_c": temperatures[i] if i < len(temperatures) and temperatures[i] is not None else None,
                    "wind_kph": (wind_speeds[i] * 3.6) if i < len(wind_speeds) and wind_speeds[i] is not None else None,  # Convert m/s to km/h
                    "precip_mm": precipitation[i] if i < len(precipitation) and precipitation[i] is not None else None,
                    "humidity_pct": humidity[i] if i < len(humidity) and humidity[i] is not None else None,
                    "condition_code": None,  # Not provided by OpenMeteo
                    "source": "openmeteo",
                    "raw_json": json.dumps(data) if len(records) == 0 else None  # Store raw data only once
                }
                records.append(record)

            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing OpenMeteo observation time {time_str}: {e}")
                continue

        logger.info(f"Normalized {len(records)} observation records from OpenMeteo")
        return records
