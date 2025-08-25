"""Analytics computation services for aggregations, accuracy, and trends."""

import logging
from datetime import datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.analytics.repositories.accuracy_repository import AccuracyRepository
from app.analytics.repositories.aggregation_repository import AggregationRepository
from app.analytics.repositories.trend_repository import TrendRepository
from app.db.models import (
    AggregationDaily,
    ForecastAccuracy,
    ForecastHourly,
    Location,
    ObservationHourly,
)

logger = structlog.get_logger(__name__)
std_logger = logging.getLogger(__name__)


class AnalyticsComputationService:
    """Service for computing analytics aggregations, accuracy, and trends."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.aggregation_repo = AggregationRepository(session)
        self.accuracy_repo = AccuracyRepository(session)
        self.trend_repo = TrendRepository(session)

    async def compute_daily_aggregations(
        self,
        location_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Compute daily aggregations from hourly observations.

        Args:
            location_id: Specific location ID or None for all locations
            start_date: Start date (defaults to 30 days ago)
            end_date: End date (defaults to yesterday)

        Returns:
            Dict with computation stats
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow() - timedelta(days=1)

        start_date = start_date.date()
        end_date = end_date.date()

        logger.info(
            "Starting daily aggregations computation",
            action="analytics.compute_daily_aggregations",
            location_id=location_id,
            start_date=str(start_date),
            end_date=str(end_date)
        )

        # Get locations to process
        if location_id:
            locations_query = select(Location).where(Location.id == location_id)
        else:
            locations_query = select(Location)

        locations_result = await self.session.execute(locations_query)
        locations = locations_result.scalars().all()

        processed_count = 0
        total_aggregations = 0

        for location in locations:
            # Process each day in the range
            current_date = start_date
            while current_date <= end_date:
                # Get hourly observations for this day
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())

                obs_query = select(ObservationHourly).where(
                    ObservationHourly.location_id == location.id,
                    ObservationHourly.observation_time >= day_start,
                    ObservationHourly.observation_time <= day_end
                )
                obs_result = await self.session.execute(obs_query)
                observations = obs_result.scalars().all()

                if not observations:
                    current_date += timedelta(days=1)
                    continue

                # Compute aggregations
                temps = [obs.temp_c for obs in observations if obs.temp_c is not None]
                precips = [obs.precip_mm for obs in observations if obs.precip_mm is not None]
                winds = [obs.wind_kph for obs in observations if obs.wind_kph is not None]
                [obs.humidity_pct for obs in observations if obs.humidity_pct is not None]

                # Calculate metrics
                avg_temp_c = sum(temps) / len(temps) if temps else None
                min_temp_c = min(temps) if temps else None
                max_temp_c = max(temps) if temps else None
                total_precip_mm = sum(precips) if precips else None
                max_wind_kph = max(winds) if winds else None

                # Calculate degree days (base temperature 18.3°C / 65°F)
                base_temp = 18.3
                heating_degree_days = None
                cooling_degree_days = None

                if avg_temp_c is not None:
                    if avg_temp_c < base_temp:
                        heating_degree_days = base_temp - avg_temp_c
                        cooling_degree_days = 0.0
                    else:
                        heating_degree_days = 0.0
                        cooling_degree_days = avg_temp_c - base_temp

                # Create or update aggregation
                await self.aggregation_repo.create_or_update(
                    location_id=location.id,
                    date=current_date,
                    temp_min_c=min_temp_c,
                    temp_max_c=max_temp_c,
                    avg_temp_c=avg_temp_c,
                    total_precip_mm=total_precip_mm,
                    max_wind_kph=max_wind_kph,
                    heating_degree_days=heating_degree_days,
                    cooling_degree_days=cooling_degree_days
                )

                total_aggregations += 1
                current_date += timedelta(days=1)

            processed_count += 1

        logger.info(
            "Daily aggregations computation completed",
            action="analytics.compute_daily_aggregations",
            processed_locations=processed_count,
            total_aggregations=total_aggregations
        )

        return {
            "processed_locations": processed_count,
            "total_aggregations": total_aggregations,
            "start_date": str(start_date),
            "end_date": str(end_date)
        }

    async def compute_forecast_accuracy(
        self,
        location_id: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None
    ) -> dict[str, Any]:
        """
        Compute forecast accuracy by comparing forecasts with observations.

        Args:
            location_id: Specific location ID or None for all locations
            start_time: Start time (defaults to 7 days ago)
            end_time: End time (defaults to now)

        Returns:
            Dict with computation stats
        """
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=7)
        if not end_time:
            end_time = datetime.utcnow()

        logger.info(
            "Starting forecast accuracy computation",
            action="analytics.compute_forecast_accuracy",
            location_id=location_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )

        # Get locations to process
        if location_id:
            locations_query = select(Location).where(Location.id == location_id)
        else:
            locations_query = select(Location)

        locations_result = await self.session.execute(locations_query)
        locations = locations_result.scalars().all()

        processed_count = 0
        total_accuracy_records = 0

        for location in locations:
            # Get forecasts in the time range
            forecast_query = select(ForecastHourly).where(
                ForecastHourly.location_id == location.id,
                ForecastHourly.target_time >= start_time,
                ForecastHourly.target_time <= end_time
            )
            forecast_result = await self.session.execute(forecast_query)
            forecasts = forecast_result.scalars().all()

            for forecast in forecasts:
                # Find matching observation
                obs_query = select(ObservationHourly).where(
                    ObservationHourly.location_id == location.id,
                    ObservationHourly.observation_time == forecast.target_time
                )
                obs_result = await self.session.execute(obs_query)
                observation = obs_result.scalar_one_or_none()

                if not observation:
                    continue

                # Check if accuracy record already exists
                existing_query = select(ForecastAccuracy).where(
                    ForecastAccuracy.location_id == location.id,
                    ForecastAccuracy.target_time == forecast.target_time,
                    ForecastAccuracy.forecast_issue_time == forecast.issue_time
                )
                existing_result = await self.session.execute(existing_query)
                existing_accuracy = existing_result.scalar_one_or_none()

                if existing_accuracy:
                    continue  # Skip if already computed

                # Compute accuracy for each variable
                variables = [
                    ("temp_c", forecast.temp_c, observation.temp_c),
                    ("precip_mm", forecast.precip_mm, observation.precip_mm),
                    ("wind_kph", forecast.wind_kph, observation.wind_kph),
                    ("humidity_pct", forecast.humidity_pct, observation.humidity_pct),
                ]

                for variable, forecast_value, observed_value in variables:
                    if forecast_value is not None or observed_value is not None:
                        await self.accuracy_repo.create(
                            location_id=location.id,
                            target_time=forecast.target_time,
                            forecast_issue_time=forecast.issue_time,
                            variable=variable,
                            forecast_value=forecast_value,
                            observed_value=observed_value
                        )
                        total_accuracy_records += 1

            processed_count += 1

        logger.info(
            "Forecast accuracy computation completed",
            action="analytics.compute_forecast_accuracy",
            processed_locations=processed_count,
            total_accuracy_records=total_accuracy_records
        )

        return {
            "processed_locations": processed_count,
            "total_accuracy_records": total_accuracy_records,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

    async def compute_trends(
        self,
        location_id: int | None = None,
        periods: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Compute trends for selected metrics across periods.

        Args:
            location_id: Specific location ID or None for all locations
            periods: List of periods to compute (e.g., ['7d', '30d'])

        Returns:
            Dict with computation stats
        """
        if not periods:
            periods = ['7d', '30d']

        logger.info(
            "Starting trends computation",
            action="analytics.compute_trends",
            location_id=location_id,
            periods=periods
        )

        # Get locations to process
        if location_id:
            locations_query = select(Location).where(Location.id == location_id)
        else:
            locations_query = select(Location)

        locations_result = await self.session.execute(locations_query)
        locations = locations_result.scalars().all()

        processed_count = 0
        total_trends = 0

        # Metrics to compute trends for
        metrics = [
            "avg_temp_c",
            "max_temp_c",
            "min_temp_c",
            "total_precip_mm",
            "max_wind_kph"
        ]

        for location in locations:
            for period in periods:
                # Calculate date ranges
                days = int(period.rstrip('d'))
                current_end = datetime.utcnow().date()
                current_start = current_end - timedelta(days=days)
                previous_end = current_start - timedelta(days=1)
                previous_start = previous_end - timedelta(days=days)

                for metric in metrics:
                    # Get current period average
                    current_query = select(func.avg(getattr(AggregationDaily, metric))).where(
                        AggregationDaily.location_id == location.id,
                        AggregationDaily.date >= current_start,
                        AggregationDaily.date <= current_end
                    )
                    current_result = await self.session.execute(current_query)
                    current_value = current_result.scalar()

                    # Get previous period average
                    previous_query = select(func.avg(getattr(AggregationDaily, metric))).where(
                        AggregationDaily.location_id == location.id,
                        AggregationDaily.date >= previous_start,
                        AggregationDaily.date <= previous_end
                    )
                    previous_result = await self.session.execute(previous_query)
                    previous_value = previous_result.scalar()

                    # Create or update trend
                    await self.trend_repo.create_or_update(
                        location_id=location.id,
                        metric=metric,
                        period=period,
                        current_value=float(current_value) if current_value is not None else None,
                        previous_value=float(previous_value) if previous_value is not None else None
                    )
                    total_trends += 1

            processed_count += 1

        logger.info(
            "Trends computation completed",
            action="analytics.compute_trends",
            processed_locations=processed_count,
            total_trends=total_trends
        )

        return {
            "processed_locations": processed_count,
            "total_trends": total_trends,
            "periods": periods,
            "metrics": metrics
        }

    async def refresh_all_analytics(
        self,
        location_id: int | None = None
    ) -> dict[str, Any]:
        """
        Run all analytics computations in sequence.

        Args:
            location_id: Specific location ID or None for all locations

        Returns:
            Dict with all computation stats
        """
        logger.info(
            "Starting full analytics refresh",
            action="analytics.refresh_all",
            location_id=location_id
        )

        start_time = datetime.utcnow()

        # Run computations in order
        aggregations_result = await self.compute_daily_aggregations(location_id=location_id)
        accuracy_result = await self.compute_forecast_accuracy(location_id=location_id)
        trends_result = await self.compute_trends(location_id=location_id)

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        result = {
            "aggregations": aggregations_result,
            "accuracy": accuracy_result,
            "trends": trends_result,
            "duration_ms": duration_ms
        }

        logger.info(
            "Full analytics refresh completed",
            action="analytics.refresh_all",
            location_id=location_id,
            duration_ms=duration_ms,
            **result
        )

        return result
