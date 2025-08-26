import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.repositories.accuracy_repository import AccuracyRepository
from app.infrastructure.db.models import ForecastHourly, ObservationHourly

logger = logging.getLogger(__name__)


class AccuracyService:
    """Service for computing forecast accuracy metrics."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.accuracy_repo = AccuracyRepository(session)

    async def compute_forecast_accuracy(
        self,
        location_id: int,
        target_time: datetime,
        forecast_issue_time: datetime
    ) -> list[Any]:
        """Compute accuracy metrics by joining forecast vs observation data."""
        logger.info(f"Computing accuracy for location {location_id} at {target_time}")

        # Get forecast record
        forecast_stmt = select(ForecastHourly).where(
            ForecastHourly.location_id == location_id,
            ForecastHourly.target_time == target_time,
            ForecastHourly.forecast_issue_time == forecast_issue_time
        )
        forecast_result = await self.session.execute(forecast_stmt)
        forecast = forecast_result.scalar_one_or_none()

        if not forecast:
            logger.warning(f"No forecast found for location {location_id} at {target_time}")
            return []

        # Get corresponding observation (within 1 hour tolerance)
        obs_stmt = select(ObservationHourly).where(
            ObservationHourly.location_id == location_id,
            ObservationHourly.observed_at >= target_time - timedelta(minutes=30),
            ObservationHourly.observed_at <= target_time + timedelta(minutes=30)
        ).order_by(ObservationHourly.observed_at).limit(1)

        obs_result = await self.session.execute(obs_stmt)
        observation = obs_result.scalar_one_or_none()

        if not observation:
            logger.warning(f"No observation found for location {location_id} near {target_time}")
            return []

        # Compute accuracy for each variable
        accuracy_records = []

        # Temperature accuracy
        if forecast.temp_c is not None or observation.temp_c is not None:
            temp_accuracy = await self.accuracy_repo.create(
                location_id=location_id,
                target_time=target_time,
                forecast_issue_time=forecast_issue_time,
                variable="temp_c",
                forecast_value=forecast.temp_c,
                observed_value=observation.temp_c
            )
            accuracy_records.append(temp_accuracy)

        # Precipitation probability vs actual precipitation
        # Convert observed precipitation to a binary (did it rain?)
        observed_precip_binary = 1.0 if (observation.precip_mm and observation.precip_mm > 0) else 0.0

        if forecast.precipitation_probability_pct is not None:
            precip_accuracy = await self.accuracy_repo.create(
                location_id=location_id,
                target_time=target_time,
                forecast_issue_time=forecast_issue_time,
                variable="precipitation_probability_pct",
                forecast_value=forecast.precipitation_probability_pct,
                observed_value=observed_precip_binary * 100  # Convert to percentage for comparison
            )
            accuracy_records.append(precip_accuracy)

        logger.info(f"Created {len(accuracy_records)} accuracy records")
        return accuracy_records

    async def compute_accuracy_for_period(
        self,
        location_id: int,
        start_time: datetime,
        end_time: datetime,
        forecast_lead_hours: int = 24
    ) -> list[Any]:
        """Compute accuracy metrics for all forecasts in a time period."""
        logger.info(f"Computing accuracy for location {location_id} from {start_time} to {end_time}")

        # Get all forecasts in the period with the specified lead time
        forecast_stmt = select(ForecastHourly).where(
            ForecastHourly.location_id == location_id,
            ForecastHourly.target_time >= start_time,
            ForecastHourly.target_time <= end_time,
            ForecastHourly.target_time - ForecastHourly.forecast_issue_time >= timedelta(hours=forecast_lead_hours - 1),
            ForecastHourly.target_time - ForecastHourly.forecast_issue_time <= timedelta(hours=forecast_lead_hours + 1)
        ).order_by(ForecastHourly.target_time)

        forecast_result = await self.session.execute(forecast_stmt)
        forecasts = list(forecast_result.scalars().all())

        all_accuracy_records = []
        for forecast in forecasts:
            accuracy_records = await self.compute_forecast_accuracy(
                location_id=location_id,
                target_time=forecast.target_time,
                forecast_issue_time=forecast.forecast_issue_time
            )
            all_accuracy_records.extend(accuracy_records)

        logger.info(f"Computed accuracy for {len(forecasts)} forecasts, created {len(all_accuracy_records)} accuracy records")
        return all_accuracy_records
