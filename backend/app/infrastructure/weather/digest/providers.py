"""Digest data providers (placeholder + real DB-backed implementations).

This consolidates previous legacy modules:
- app.services.digest_providers (placeholder providers)
- app.services.digest_real_providers (database-backed providers)

New architecture: infrastructure layer exposes concrete providers used by
application use cases (e.g., GenerateDigestUseCase). Tests should import from
`app.infrastructure.weather.digest.providers`.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.models import ForecastHourly, UserPreferences, Location

logger = structlog.get_logger(__name__)


# ---------------- Placeholder Providers (for tests / early environments) -----

class PlaceholderForecastProvider:
    """Generate synthetic hourly forecast data for a 24h window."""

    async def get_forecast(self, location_id: int, date: str) -> dict[str, Any]:
        base_date = datetime.strptime(date, "%Y-%m-%d")
        hourly_data: list[dict[str, Any]] = []
        base_temp = 18 + random.gauss(0, 5)
        for hour in range(24):
            hour_time = base_date + timedelta(hours=hour)
            temp_variation = 5 * (1 + 0.8 * (hour - 12) / 12) if 6 < hour < 18 else -2
            temperature = base_temp + temp_variation + random.gauss(0, 1)
            precip_chance = 0.3 if 14 <= hour <= 18 else 0.1
            precipitation = random.uniform(0, 5) if random.random() < precip_chance else 0
            wind_speed = random.uniform(5, 25) + (3 if precipitation > 0 else 0)
            humidity = random.uniform(40, 85) + (10 if precipitation > 0 else 0)
            humidity = min(100, humidity)
            hourly_data.append(
                {
                    "time": hour_time.isoformat(),
                    "temperature": round(temperature, 1),
                    "precipitation": round(precipitation, 1),
                    "wind_speed": round(wind_speed, 1),
                    "humidity": round(humidity, 1),
                }
            )
        return {
            "location_id": location_id,
            "date": date,
            "last_updated": datetime.utcnow().isoformat(),
            "hourly": hourly_data,
        }


class PlaceholderPreferencesProvider:
    """Return deterministic synthetic user preferences."""

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        user_hash = hash(user_id) % 1000
        return {
            "outdoor_activities": user_hash % 3 != 0,
            "temperature_tolerance": ["low", "normal", "high"][user_hash % 3],
            "rain_tolerance": ["low", "normal", "high"][(user_hash // 3) % 3],
            "units_system": "metric",
            "time_zone": "UTC",
            "activity_preferences": (
                ["walking", "cycling", "gardening"]
                if user_hash % 2 == 0
                else ["reading", "cooking", "indoor_exercise"]
            ),
        }


# ---------------- Real / Database-backed Providers --------------------------

class DatabaseForecastProvider:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_forecast(self, location_id: int, date: str) -> dict[str, Any]:
        logger.debug("Fetching forecast from DB", action="digest.db_forecast.fetch", location_id=location_id, date=date)
        target_date = datetime.strptime(date, "%Y-%m-%d")
        start_time = target_date
        end_time = target_date + timedelta(days=1)
        try:
            result = await self.session.execute(
                select(ForecastHourly).where(
                    ForecastHourly.location_id == location_id,
                    ForecastHourly.forecast_time >= start_time,
                    ForecastHourly.forecast_time < end_time,
                ).order_by(ForecastHourly.forecast_time)
            )
            records = result.scalars().all()
            if not records:
                raise ValueError(f"No forecast data for location {location_id} on {date}")
            hourly = [
                {
                    "time": r.forecast_time.isoformat(),
                    "temperature": r.temperature_2m,
                    "precipitation": r.precipitation,
                    "wind_speed": r.wind_speed_10m,
                    "humidity": r.relative_humidity_2m or 50,
                }
                for r in records
            ]
            return {
                "location_id": location_id,
                "date": date,
                "last_updated": datetime.utcnow().isoformat(),
                "hourly": hourly,
            }
        except Exception as e:  # noqa: BLE001
            logger.error("Forecast fetch failed", action="digest.db_forecast.error", error=str(e))
            raise


class DatabasePreferencesProvider:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        logger.debug("Fetching preferences", action="digest.db_prefs.fetch", user_id=user_id)
        try:
            user_id_int = int(user_id) if user_id.isdigit() else None
            if user_id_int is None:
                return self._defaults()
            result = await self.session.execute(select(UserPreferences).where(UserPreferences.user_id == user_id_int))
            record = result.scalar_one_or_none()
            if not record:
                return self._defaults()
            return {
                "outdoor_activities": record.outdoor_activities,
                "temperature_tolerance": record.temperature_tolerance or "normal",
                "rain_tolerance": record.rain_tolerance or "low",
                "units_system": record.units_system or "metric",
                "time_zone": record.timezone or "UTC",
                "activity_preferences": self._activity_prefs(record),
            }
        except Exception as e:  # noqa: BLE001
            logger.error("Preferences fetch failed", action="digest.db_prefs.error", error=str(e))
            return self._defaults()

    def _defaults(self) -> dict[str, Any]:
        return {
            "outdoor_activities": True,
            "temperature_tolerance": "normal",
            "rain_tolerance": "low",
            "units_system": "metric",
            "time_zone": "UTC",
            "activity_preferences": ["walking", "cycling", "gardening"],
        }

    def _activity_prefs(self, record: UserPreferences) -> list[str]:  # pragma: no cover simple mapping
        return ["walking", "cycling", "gardening"] if record.outdoor_activities else ["reading", "cooking", "indoor_exercise"]


class EnhancedLocationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_primary_location(self, user_id: str) -> int:
        try:
            user_id_int = int(user_id) if user_id.isdigit() else None
            if user_id_int is None:
                raise ValueError("Invalid user ID format")
            result = await self.session.execute(
                select(Location).where(Location.user_id == user_id_int).order_by(Location.id).limit(1)
            )
            loc = result.scalar_one_or_none()
            if not loc:
                return 1  # fallback default
            return loc.id
        except Exception as e:  # noqa: BLE001
            logger.warning("Primary location fallback", action="digest.location.fallback", error=str(e))
            return 1


__all__ = [
    "PlaceholderForecastProvider",
    "PlaceholderPreferencesProvider",
    "DatabaseForecastProvider",
    "DatabasePreferencesProvider",
    "EnhancedLocationService",
]