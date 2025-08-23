"""OpenMeteo air quality provider implementation."""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.ingest.providers import AirQualityProvider

logger = logging.getLogger(__name__)


class OpenMeteoAirQualityProvider(AirQualityProvider):
    """OpenMeteo air quality provider using free API."""

    def __init__(self):
        self.base_url = settings.openmeteo_base_url
        self.timeout = 30.0

    @property
    def provider_name(self) -> str:
        return "openmeteo"

    async def fetch_air_quality(self, location_id: int, lat: float, lon: float, hours_back: int = 24) -> list[dict[str, Any]]:
        """Fetch air quality data from OpenMeteo air quality API."""
        logger.info(f"Fetching OpenMeteo air quality for location {location_id} at {lat}, {lon} ({hours_back} hours back)")

        # OpenMeteo air quality endpoint
        url = f"{self.base_url}/v1/air-quality"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "pm10,pm2_5,ozone,nitrogen_dioxide,sulphur_dioxide,alder_pollen,birch_pollen,grass_pollen,ragweed_pollen",
            "past_days": min(7, max(1, hours_back // 24 + 1)),  # Limit to max 7 days past data
            "forecast_days": 0,  # Only historical data
            "timezone": "UTC"
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                return self._normalize_air_quality_data(location_id, data, hours_back)

            except httpx.RequestError as e:
                logger.error(f"Network error fetching OpenMeteo air quality for location {location_id}: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching OpenMeteo air quality for location {location_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching OpenMeteo air quality for location {location_id}: {e}")
                raise

    def _normalize_air_quality_data(self, location_id: int, data: dict[str, Any], hours_back: int) -> list[dict[str, Any]]:
        """Normalize OpenMeteo air quality response to our standard format."""
        hourly = data.get("hourly", {})
        
        times = hourly.get("time", [])
        pm10 = hourly.get("pm10", [])
        pm2_5 = hourly.get("pm2_5", [])
        ozone = hourly.get("ozone", [])
        no2 = hourly.get("nitrogen_dioxide", [])
        so2 = hourly.get("sulphur_dioxide", [])
        
        # Pollen data - combine different tree types
        alder_pollen = hourly.get("alder_pollen", [])
        birch_pollen = hourly.get("birch_pollen", [])
        grass_pollen = hourly.get("grass_pollen", [])
        ragweed_pollen = hourly.get("ragweed_pollen", [])

        # Filter to only include data within our requested time range
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        records = []
        for i, time_str in enumerate(times):
            try:
                # Parse ISO timestamp
                observed_at = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                
                # Skip if outside our time range or future data
                if observed_at < cutoff_time or observed_at > datetime.now(timezone.utc):
                    continue

                # Combine tree pollen (take max of available tree types)
                tree_pollen = None
                tree_values = [
                    alder_pollen[i] if i < len(alder_pollen) and alder_pollen[i] is not None else 0,
                    birch_pollen[i] if i < len(birch_pollen) and birch_pollen[i] is not None else 0
                ]
                if any(v > 0 for v in tree_values):
                    tree_pollen = max(tree_values)
                
                record = {
                    "location_id": location_id,
                    "observed_at": observed_at,
                    "pm10": pm10[i] if i < len(pm10) and pm10[i] is not None else None,
                    "pm2_5": pm2_5[i] if i < len(pm2_5) and pm2_5[i] is not None else None,
                    "ozone": ozone[i] if i < len(ozone) and ozone[i] is not None else None,
                    "no2": no2[i] if i < len(no2) and no2[i] is not None else None,
                    "so2": so2[i] if i < len(so2) and so2[i] is not None else None,
                    "pollen_tree": tree_pollen,
                    "pollen_grass": grass_pollen[i] if i < len(grass_pollen) and grass_pollen[i] is not None else None,
                    "pollen_weed": ragweed_pollen[i] if i < len(ragweed_pollen) and ragweed_pollen[i] is not None else None,
                    "source": "openmeteo",
                    "raw_json": json.dumps(data) if len(records) == 0 else None  # Store raw data only once
                }
                records.append(record)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing OpenMeteo air quality time {time_str}: {e}")
                continue

        logger.info(f"Normalized {len(records)} air quality records from OpenMeteo")
        return records