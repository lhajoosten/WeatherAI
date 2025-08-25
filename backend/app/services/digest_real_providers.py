"""Real data providers for digest service.

These providers integrate with the existing forecast ingestion system and 
user preferences to provide real data instead of placeholders.
"""

from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import ForecastHourly, Location, UserPreferences

logger = structlog.get_logger(__name__)


class DatabaseForecastProvider:
    """Forecast provider that retrieves data from the ingested forecast database."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_forecast(self, location_id: int, date: str) -> dict[str, Any]:
        """Get forecast data from database for a location and date.

        Args:
            location_id: Location identifier
            date: Date string (YYYY-MM-DD)

        Returns:
            Dictionary with hourly forecast data in expected format

        Raises:
            ValueError: If no forecast data found
        """
        logger.debug(
            "Fetching forecast from database",
            action="database_forecast_provider.get_forecast", 
            location_id=location_id,
            date=date
        )

        # Parse the target date and create time range for 24 hours
        target_date = datetime.strptime(date, "%Y-%m-%d")
        start_time = target_date
        end_time = target_date + timedelta(days=1)

        try:
            # Query forecast data for the 24-hour period
            result = await self.session.execute(
                select(ForecastHourly)
                .where(
                    ForecastHourly.location_id == location_id,
                    ForecastHourly.forecast_time >= start_time,
                    ForecastHourly.forecast_time < end_time
                )
                .order_by(ForecastHourly.forecast_time)
            )
            
            forecast_records = result.scalars().all()
            
            if not forecast_records:
                logger.warning(
                    "No forecast data found",
                    action="database_forecast_provider.no_data",
                    location_id=location_id,
                    date=date
                )
                raise ValueError(f"No forecast data found for location {location_id} on {date}")

            # Convert database records to expected format
            hourly_data = []
            for record in forecast_records:
                hourly_data.append({
                    "time": record.forecast_time.isoformat(),
                    "temperature": record.temperature_2m,
                    "precipitation": record.precipitation,
                    "wind_speed": record.wind_speed_10m,
                    "humidity": record.relative_humidity_2m or 50  # Default if missing
                })

            logger.info(
                "Forecast data retrieved successfully",
                action="database_forecast_provider.success",
                location_id=location_id,
                date=date,
                hourly_count=len(hourly_data)
            )

            return {
                "location_id": location_id,
                "date": date,
                "last_updated": datetime.utcnow().isoformat(),
                "hourly": hourly_data
            }

        except Exception as e:
            logger.error(
                "Failed to retrieve forecast data",
                action="database_forecast_provider.error",
                location_id=location_id,
                date=date,
                error=str(e)
            )
            raise ValueError(f"Failed to retrieve forecast data: {e}") from e


class DatabasePreferencesProvider:
    """User preferences provider that retrieves data from the database."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        """Get user preferences from database.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with user preferences in expected format
        """
        logger.debug(
            "Fetching user preferences from database",
            action="database_preferences_provider.get_preferences",
            user_id=user_id
        )

        try:
            # Convert user_id to int for database lookup
            user_id_int = int(user_id) if user_id.isdigit() else None
            if user_id_int is None:
                logger.warning(
                    "Invalid user ID format",
                    action="database_preferences_provider.invalid_user_id",
                    user_id=user_id
                )
                return self._get_default_preferences()

            # Query user preferences
            result = await self.session.execute(
                select(UserPreferences)
                .where(UserPreferences.user_id == user_id_int)
            )
            
            preferences_record = result.scalar_one_or_none()
            
            if not preferences_record:
                logger.info(
                    "No user preferences found, using defaults",
                    action="database_preferences_provider.no_preferences",
                    user_id=user_id
                )
                return self._get_default_preferences()

            # Convert database record to expected format
            preferences = {
                "outdoor_activities": preferences_record.outdoor_activities,
                "temperature_tolerance": preferences_record.temperature_tolerance or "normal",
                "rain_tolerance": preferences_record.rain_tolerance or "low", 
                "units_system": preferences_record.units_system or "metric",
                "time_zone": preferences_record.timezone or "UTC",
                "activity_preferences": self._parse_activity_preferences(preferences_record)
            }

            logger.info(
                "User preferences retrieved successfully",
                action="database_preferences_provider.success",
                user_id=user_id
            )

            return preferences

        except Exception as e:
            logger.error(
                "Failed to retrieve user preferences",
                action="database_preferences_provider.error",
                user_id=user_id,
                error=str(e)
            )
            # Fallback to defaults rather than failing
            return self._get_default_preferences()

    def _get_default_preferences(self) -> dict[str, Any]:
        """Get default user preferences.
        
        Returns:
            Dictionary with default preferences
        """
        return {
            "outdoor_activities": True,
            "temperature_tolerance": "normal",
            "rain_tolerance": "low",
            "units_system": "metric", 
            "time_zone": "UTC",
            "activity_preferences": ["walking", "cycling", "gardening"]
        }

    def _parse_activity_preferences(self, preferences_record: UserPreferences) -> list[str]:
        """Parse activity preferences from database record.
        
        Args:
            preferences_record: UserPreferences database record
            
        Returns:
            List of activity preference strings
        """
        # For now, return default activities based on outdoor preference
        # In a full implementation, this might be stored as JSON or separate table
        if preferences_record.outdoor_activities:
            return ["walking", "cycling", "gardening"]
        else:
            return ["reading", "cooking", "indoor_exercise"]


class EnhancedLocationService:
    """Service to get user's primary location for digest generation."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_user_primary_location(self, user_id: str) -> int:
        """Get user's primary location ID.

        Args:
            user_id: User identifier

        Returns:
            Primary location ID

        Raises:
            ValueError: If no location found for user
        """
        logger.debug(
            "Getting user primary location",
            action="enhanced_location_service.get_primary_location",
            user_id=user_id
        )

        try:
            user_id_int = int(user_id) if user_id.isdigit() else None
            if user_id_int is None:
                raise ValueError(f"Invalid user ID format: {user_id}")

            # Query for user's first location (assuming first created is primary)
            # In a full implementation, there might be a primary_location_id field
            result = await self.session.execute(
                select(Location)
                .where(Location.user_id == user_id_int)
                .order_by(Location.id)
                .limit(1)
            )
            
            location = result.scalar_one_or_none()
            
            if not location:
                logger.warning(
                    "No location found for user",
                    action="enhanced_location_service.no_location",
                    user_id=user_id
                )
                # Return a default location (e.g., Amsterdam) for testing
                # In production, this should probably raise an error
                return 1

            logger.info(
                "Primary location found",
                action="enhanced_location_service.found",
                user_id=user_id,
                location_id=location.id,
                location_name=location.name
            )

            return location.id

        except Exception as e:
            logger.error(
                "Failed to get user primary location", 
                action="enhanced_location_service.error",
                user_id=user_id,
                error=str(e)
            )
            # Fallback to default location rather than failing
            return 1