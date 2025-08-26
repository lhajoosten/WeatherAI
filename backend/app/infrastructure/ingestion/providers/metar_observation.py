"""METAR observation provider implementation (optional, config-enabled)."""
import json
import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.settings import settings
from app.infrastructure.ingestion.providers import ObservationProvider

logger = logging.getLogger(__name__)


class MetarObservationProvider(ObservationProvider):
    """METAR observation provider using NOAA Aviation Weather Service."""

    def __init__(self):
        self.base_url = settings.metar_base_url
        self.timeout = 30.0
        self.enabled = settings.enable_metar

    @property
    def provider_name(self) -> str:
        return "metar"

    async def fetch_observations(self, location_id: int, lat: float, lon: float, hours_back: int = 24) -> list[dict[str, Any]]:
        """Fetch METAR observation data from NOAA."""
        if not self.enabled:
            logger.info("METAR ingestion is disabled")
            return []

        logger.info(f"Fetching METAR observations for location {location_id} at {lat}, {lon} ({hours_back} hours back)")

        # Calculate time range
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=hours_back)

        # NOAA METAR API parameters
        params = {
            "dataSource": "metars",
            "requestType": "retrieve",
            "format": "xml",
            "boundingBox": f"{lat-0.5},{lon-0.5},{lat+0.5},{lon+0.5}",  # 1-degree box around location
            "startTime": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endTime": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "hoursBeforeNow": hours_back
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()

                return self._parse_metar_xml(location_id, response.text)

            except httpx.RequestError as e:
                logger.error(f"Network error fetching METAR for location {location_id}: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching METAR for location {location_id}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching METAR for location {location_id}: {e}")
                raise

    def _parse_metar_xml(self, location_id: int, xml_text: str) -> list[dict[str, Any]]:
        """Parse METAR XML response to normalized format."""
        try:
            root = ET.fromstring(xml_text)
            records = []

            # Find all METAR elements
            for metar in root.findall(".//METAR"):
                try:
                    record = self._parse_single_metar(location_id, metar)
                    if record:
                        records.append(record)
                except Exception as e:
                    logger.warning(f"Error parsing METAR record: {e}")
                    continue

            logger.info(f"Parsed {len(records)} METAR records")
            return records

        except ET.ParseError as e:
            logger.error(f"Error parsing METAR XML: {e}")
            return []

    def _parse_single_metar(self, location_id: int, metar_elem: ET.Element) -> dict[str, Any] | None:
        """Parse a single METAR XML element."""
        try:
            # Parse observation time
            obs_time_elem = metar_elem.find("observation_time")
            if obs_time_elem is None or obs_time_elem.text is None:
                return None

            observed_at = datetime.fromisoformat(obs_time_elem.text.replace('Z', '+00:00'))

            # Parse temperature (Celsius)
            temp_c = None
            temp_elem = metar_elem.find("temp_c")
            if temp_elem is not None and temp_elem.text:
                temp_c = float(temp_elem.text)

            # Parse wind speed (convert knots to km/h)
            wind_kph = None
            wind_speed_elem = metar_elem.find("wind_speed_kt")
            if wind_speed_elem is not None and wind_speed_elem.text:
                wind_speed_kt = float(wind_speed_elem.text)
                wind_kph = wind_speed_kt * 1.852  # Convert knots to km/h

            # Parse visibility (convert statute miles to meters, then store visibility_km)
            visibility_km = None
            visibility_elem = metar_elem.find("visibility_statute_mi")
            if visibility_elem is not None and visibility_elem.text:
                visibility_mi = float(visibility_elem.text)
                visibility_km = visibility_mi * 1.60934  # Convert miles to km

            # Parse humidity
            humidity_pct = None
            humidity_elem = metar_elem.find("relative_humidity")
            if humidity_elem is not None and humidity_elem.text:
                humidity_pct = float(humidity_elem.text)

            # Parse precipitation (limited info from METAR)
            precip_mm = None
            # METAR doesn't provide direct precipitation amounts typically

            # Parse weather condition
            condition_code = None
            weather_elem = metar_elem.find("wx_string")
            if weather_elem is not None and weather_elem.text:
                condition_code = weather_elem.text

            # Store station ID and raw METAR for debugging
            station_id = None
            station_elem = metar_elem.find("station_id")
            if station_elem is not None and station_elem.text:
                station_id = station_elem.text

            raw_metar = None
            raw_elem = metar_elem.find("raw_text")
            if raw_elem is not None and raw_elem.text:
                raw_metar = raw_elem.text

            record = {
                "location_id": location_id,
                "observed_at": observed_at,
                "temp_c": temp_c,
                "wind_kph": wind_kph,
                "precip_mm": precip_mm,
                "humidity_pct": humidity_pct,
                "condition_code": condition_code,
                "source": "metar",
                "raw_json": json.dumps({
                    "station_id": station_id,
                    "raw_metar": raw_metar,
                    "visibility_km": visibility_km
                })
            }

            return record

        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing METAR element: {e}")
            return None
