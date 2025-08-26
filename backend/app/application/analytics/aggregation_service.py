import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.repositories.analytics.aggregation_repository import AggregationRepository
from app.infrastructure.db.models import ObservationHourly

logger = logging.getLogger(__name__)


class AggregationService:
    """Service for computing daily aggregates from hourly observations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.aggregation_repo = AggregationRepository(session)

    async def compute_daily_aggregations(
        self,
        location_id: int,
        date: datetime,
        base_temp_c: float = 18.0  # Base temperature for degree days
    ) -> Any | None:
        """Compute daily aggregates from hourly observations for a specific date.

        Idempotent - will update existing record if present.
        """
        logger.info(f"Computing daily aggregations for location {location_id}, date {date.date()}")

        # Get start and end of day (UTC)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)

        # Query hourly observations for the day
        stmt = select(ObservationHourly).where(
            ObservationHourly.location_id == location_id,
            ObservationHourly.observed_at >= start_of_day,
            ObservationHourly.observed_at <= end_of_day
        )
        result = await self.session.execute(stmt)
        observations = list(result.scalars().all())

        if not observations:
            logger.warning(f"No observations found for location {location_id} on {date.date()}")
            return None

        # Compute aggregates
        temps = [obs.temp_c for obs in observations if obs.temp_c is not None]
        precips = [obs.precip_mm for obs in observations if obs.precip_mm is not None]
        winds = [obs.wind_kph for obs in observations if obs.wind_kph is not None]

        temp_min_c = min(temps) if temps else None
        temp_max_c = max(temps) if temps else None
        avg_temp_c = sum(temps) / len(temps) if temps else None
        total_precip_mm = sum(precips) if precips else None
        max_wind_kph = max(winds) if winds else None

        # Compute degree days
        heating_degree_days = None
        cooling_degree_days = None

        if avg_temp_c is not None:
            if avg_temp_c < base_temp_c:
                heating_degree_days = base_temp_c - avg_temp_c
                cooling_degree_days = 0.0
            else:
                heating_degree_days = 0.0
                cooling_degree_days = avg_temp_c - base_temp_c

        # Store aggregation (idempotent)
        aggregation = await self.aggregation_repo.create_or_update(
            location_id=location_id,
            date=start_of_day,
            temp_min_c=temp_min_c,
            temp_max_c=temp_max_c,
            avg_temp_c=avg_temp_c,
            total_precip_mm=total_precip_mm,
            max_wind_kph=max_wind_kph,
            heating_degree_days=heating_degree_days,
            cooling_degree_days=cooling_degree_days
        )

        logger.info(f"Computed daily aggregation: {aggregation.id} for {date.date()}")
        return aggregation

    async def compute_aggregations_for_period(
        self,
        location_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> list[Any]:
        """Compute daily aggregations for a date range."""
        logger.info(f"Computing aggregations for location {location_id} from {start_date.date()} to {end_date.date()}")

        aggregations = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        while current_date <= end_date:
            aggregation = await self.compute_daily_aggregations(location_id, current_date)
            if aggregation:
                aggregations.append(aggregation)
            current_date += timedelta(days=1)

        logger.info(f"Computed {len(aggregations)} daily aggregations")
        return aggregations
