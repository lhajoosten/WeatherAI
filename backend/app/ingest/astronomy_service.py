"""Astronomy computation service using astral library."""
import logging
from datetime import date, datetime, timezone
from typing import Any

from astral import LocationInfo
from astral.sun import sun
from astral.moon import phase

logger = logging.getLogger(__name__)


class AstronomyComputationService:
    """Service for computing astronomical data locally."""

    def compute_astronomy_daily(self, location_id: int, lat: float, lon: float, target_date: date) -> dict[str, Any]:
        """Compute astronomical data for a location and date.
        
        Args:
            location_id: Database location ID
            lat: Latitude
            lon: Longitude
            target_date: Date to compute astronomy for
            
        Returns:
            Dictionary with astronomy data
        """
        logger.info(f"Computing astronomy for location {location_id} at {lat}, {lon} for {target_date}")

        try:
            # Create astral location
            location = LocationInfo("Custom", "Region", "UTC", lat, lon)
            
            # Calculate sun times
            sun_data = sun(location.observer, date=target_date)
            
            sunrise_utc = sun_data['sunrise'].replace(tzinfo=timezone.utc)
            sunset_utc = sun_data['sunset'].replace(tzinfo=timezone.utc)
            civil_twilight_start = sun_data['dawn'].replace(tzinfo=timezone.utc)
            civil_twilight_end = sun_data['dusk'].replace(tzinfo=timezone.utc)
            
            # Calculate daylight minutes
            daylight_duration = sunset_utc - sunrise_utc
            daylight_minutes = int(daylight_duration.total_seconds() / 60)
            
            # Calculate moon phase (0.0 = new moon, 1.0 = full moon)
            moon_phase_value = phase(target_date) / 28.0  # Normalize to 0-1 range
            
            record = {
                "location_id": location_id,
                "date": datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                "sunrise_utc": sunrise_utc,
                "sunset_utc": sunset_utc,
                "daylight_minutes": daylight_minutes,
                "moon_phase": round(moon_phase_value, 3),
                "civil_twilight_start_utc": civil_twilight_start,
                "civil_twilight_end_utc": civil_twilight_end,
                "generated_at": datetime.now(timezone.utc)
            }
            
            logger.info(f"Computed astronomy data: sunrise={sunrise_utc}, sunset={sunset_utc}, daylight={daylight_minutes}min, moon_phase={record['moon_phase']}")
            return record
            
        except Exception as e:
            logger.error(f"Error computing astronomy for location {location_id}: {e}")
            raise