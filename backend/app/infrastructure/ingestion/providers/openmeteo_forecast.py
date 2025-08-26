"""OpenMeteo forecast provider implementation."""
import json
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.settings import settings
from app.core.datetime_utils import parse_iso_utc
from app.infrastructure.ingestion.providers import ForecastProvider

logger = logging.getLogger(__name__)


class OpenMeteoForecastProvider(ForecastProvider):
    """OpenMeteo forecast provider using free API."""

    def __init__(self):
        self.base_url = settings.openmeteo_base_url
        self.timeout = 30.0

    @property
    def provider_name(self) -> str:
        return "openmeteo"

    async def fetch_forecast(self, location_id: int, lat: float, lon: float) -> list[dict[str, Any]]:
        """Fetch forecast data from OpenMeteo API."""
        logger.info(f"Fetching OpenMeteo forecast for location {location_id} at {lat}, {lon}")

        # OpenMeteo forecast endpoint with hourly data
        url = f"{self.base_url}/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation_probability,wind_speed_10m",
            "forecast_days": 3,  # 3 days of forecast
            "timezone": "UTC"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                return self._normalize_forecast_data(location_id, data)

            except httpx.RequestError as e:
                logger.error(f"Network error fetching OpenMeteo forecast for location {location_id}: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching OpenMeteo forecast for location {location_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching OpenMeteo forecast for location {location_id}: {e}")
                raise

    def _normalize_forecast_data(self, location_id: int, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Normalize OpenMeteo forecast response to our standard format."""
        forecast_issue_time = datetime.now(UTC)
        hourly = data.get("hourly", {})

        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        precip_probs = hourly.get("precipitation_probability", [])
        wind_speeds = hourly.get("wind_speed_10m", [])

        records = []
        for i, time_str in enumerate(times):
            try:
                # Use centralized datetime parsing for consistency
                target_time = parse_iso_utc(time_str)

                record = {
                    "location_id": location_id,
                    "forecast_issue_time": forecast_issue_time,
                    "target_time": target_time,
                    "temp_c": temperatures[i] if i < len(temperatures) and temperatures[i] is not None else None,
                    "precipitation_probability_pct": precip_probs[i] if i < len(precip_probs) and precip_probs[i] is not None else None,
                    "wind_kph": (wind_speeds[i] * 3.6) if i < len(wind_speeds) and wind_speeds[i] is not None else None,  # Convert m/s to km/h
                    "model_name": "openmeteo_v1",
                    "source_run_id": f"openmeteo_{forecast_issue_time.strftime('%Y%m%d_%H')}",
                    "raw_json": json.dumps(data) if len(records) == 0 else None  # Store raw data only once
                }
                records.append(record)

            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing OpenMeteo forecast time {time_str}: {e}")
                continue

        logger.info(f"Normalized {len(records)} forecast records from OpenMeteo")
        return records
