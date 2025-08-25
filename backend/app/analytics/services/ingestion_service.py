import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.repositories.forecast_repository import ForecastRepository
from app.analytics.repositories.observation_repository import ObservationRepository

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting weather data into normalized analytics tables.

    Phase 1: Stub implementation with mock data generation.
    TODO: Integrate with real weather providers (Open-Meteo, NOAA).
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.observation_repo = ObservationRepository(session)
        self.forecast_repo = ForecastRepository(session)

    async def ingest_mock_observations(self, location_id: int, hours_back: int = 24) -> list[Any]:
        """Generate mock observation data for testing.

        TODO: Replace with real provider integration.
        """
        logger.info(f"Generating {hours_back} hours of mock observations for location {location_id}")

        observations = []
        base_temp = 20.0  # Base temperature in Celsius

        for hour_offset in range(hours_back):
            observed_at = datetime.utcnow() - timedelta(hours=hour_offset)

            # Generate realistic mock data with daily/hourly variation
            hour_of_day = observed_at.hour
            daily_temp_variation = 5 * (1 - abs(hour_of_day - 14) / 14)  # Peak at 2 PM
            temp_c = base_temp + daily_temp_variation + (hour_offset * 0.1)  # Slight trend

            observation = await self.observation_repo.create(
                location_id=location_id,
                observed_at=observed_at,
                temp_c=round(temp_c, 1),
                wind_kph=round(10 + (hour_offset % 20), 1),
                precip_mm=0.1 if hour_offset % 8 == 0 else 0.0,  # Rain every 8 hours
                humidity_pct=60 + (hour_offset % 30),
                condition_code="clear" if hour_offset % 4 else "cloudy",
                source="mock"
            )
            observations.append(observation)

        logger.info(f"Created {len(observations)} mock observations")
        return observations

    async def ingest_mock_forecasts(self, location_id: int, hours_ahead: int = 48) -> list[Any]:
        """Generate mock forecast data for testing.

        TODO: Replace with real provider ingestion from ForecastCache.
        """
        logger.info(f"Generating {hours_ahead} hours of mock forecasts for location {location_id}")

        forecasts = []
        issue_time = datetime.utcnow()
        base_temp = 22.0  # Slightly different from observations for accuracy testing

        for hour_offset in range(hours_ahead):
            target_time = issue_time + timedelta(hours=hour_offset)

            # Generate mock forecast with slight bias vs observations
            hour_of_day = target_time.hour
            daily_temp_variation = 4.5 * (1 - abs(hour_of_day - 14) / 14)  # Slightly underestimate
            temp_c = base_temp + daily_temp_variation + (hour_offset * 0.05)

            forecast = await self.forecast_repo.create(
                location_id=location_id,
                forecast_issue_time=issue_time,
                target_time=target_time,
                temp_c=round(temp_c, 1),
                precipitation_probability_pct=20 if hour_offset % 6 == 0 else 5,
                wind_kph=round(12 + (hour_offset % 15), 1),
                model_name="mock_model_v1",
                source_run_id=f"mock_run_{issue_time.strftime('%Y%m%d_%H')}"
            )
            forecasts.append(forecast)

        logger.info(f"Created {len(forecasts)} mock forecasts")
        return forecasts

    async def count_observations_in_range(
        self, location_id: int, start_date: datetime, end_date: datetime
    ) -> int:
        """Count existing observations in date range for idempotent seeding."""
        return await self.observation_repo.count_by_date_range(
            location_id, start_date, end_date
        )

    async def create_synthetic_observation(
        self, location_id: int, observed_at: datetime
    ) -> Any:
        """Create a single synthetic observation record."""
        # Generate realistic mock data with daily/hourly variation
        hour_of_day = observed_at.hour
        day_of_year = observed_at.timetuple().tm_yday

        # Base temperature varies by season and time of day
        seasonal_temp = 20.0 + 10 * (1 - abs(day_of_year - 182) / 182)  # Peak in summer
        daily_temp_variation = 8 * (1 - abs(hour_of_day - 14) / 14)  # Peak at 2 PM
        base_temp = seasonal_temp + daily_temp_variation

        # Add some randomness based on time to make data realistic
        time_seed = hash(observed_at.isoformat()) % 100 / 100.0
        temp_noise = (time_seed - 0.5) * 4  # ±2°C variation

        observation = await self.observation_repo.create(
            location_id=location_id,
            observed_at=observed_at,
            temp_c=round(base_temp + temp_noise, 1),
            wind_kph=round(8 + time_seed * 15, 1),  # 8-23 kph
            precip_mm=0.2 if time_seed > 0.8 else 0.0,  # 20% chance of rain
            humidity_pct=int(50 + time_seed * 40),  # 50-90%
            condition_code="rain" if time_seed > 0.9 else ("cloudy" if time_seed > 0.6 else "clear"),
            source="synthetic"
        )
        return observation

    async def create_synthetic_forecast(
        self, location_id: int, forecast_issue_time: datetime, target_time: datetime
    ) -> Any:
        """Create a single synthetic forecast record."""
        # Generate forecast data that's slightly different from observations
        time_seed = hash(f"{forecast_issue_time.isoformat()}-{target_time.isoformat()}") % 100 / 100.0
        lead_hours = (target_time - forecast_issue_time).total_seconds() / 3600

        # Forecast accuracy decreases with lead time
        accuracy_factor = max(0.7, 1.0 - (lead_hours / 168))  # Degrades over a week

        hour_of_day = target_time.hour
        day_of_year = target_time.timetuple().tm_yday

        # Similar base calculation as observations but with forecast uncertainty
        seasonal_temp = 20.0 + 10 * (1 - abs(day_of_year - 182) / 182)
        daily_temp_variation = 8 * (1 - abs(hour_of_day - 14) / 14)
        base_temp = seasonal_temp + daily_temp_variation

        # Add forecast uncertainty
        forecast_error = (time_seed - 0.5) * 6 * (1 - accuracy_factor)  # More error with longer lead

        forecast = await self.forecast_repo.create(
            location_id=location_id,
            forecast_issue_time=forecast_issue_time,
            target_time=target_time,
            temp_c=round(base_temp + forecast_error, 1),
            precipitation_probability_pct=int(time_seed * 100) if time_seed > 0.7 else 0,
            wind_kph=round(10 + time_seed * 20, 1),
            model_name="synthetic_model",
            source_run_id=f"synthetic_{forecast_issue_time.strftime('%Y%m%d_%H')}",
            raw_json='{"source": "synthetic"}'
        )
        return forecast
