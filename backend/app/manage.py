"""Management commands for WeatherAI backend."""

import asyncio
from datetime import datetime, timedelta

import structlog
import typer

from app.analytics.services.computation_service import AnalyticsComputationService
from app.analytics.services.ingestion_service import IngestionService
from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.db.repositories import LocationRepository

logger = structlog.get_logger(__name__)

app = typer.Typer()


@app.command()
def seed_data(
    days: int = typer.Option(7, help="Number of days of data to seed"),
    locations: str = typer.Option("all", help="Location IDs (comma-separated) or 'all'"),
    no_refresh: bool = typer.Option(False, help="Skip analytics refresh after seeding")
):
    """Seed synthetic observation and forecast data for development."""
    asyncio.run(_seed_data_async(days, locations, no_refresh))


@app.command()
def compute_aggregations(
    location_id: int | None = typer.Option(None, help="Specific location ID or all locations"),
    days: int = typer.Option(30, help="Number of days back to compute")
):
    """Compute daily aggregations from hourly observations."""
    asyncio.run(_compute_aggregations_async(location_id, days))


@app.command()
def compute_accuracy(
    location_id: int | None = typer.Option(None, help="Specific location ID or all locations"),
    days: int = typer.Option(7, help="Number of days back to compute")
):
    """Compute forecast accuracy metrics."""
    asyncio.run(_compute_accuracy_async(location_id, days))


@app.command()
def compute_trends(
    location_id: int | None = typer.Option(None, help="Specific location ID or all locations"),
    periods: str = typer.Option("7d,30d", help="Comma-separated periods (e.g., '7d,30d')")
):
    """Compute trend metrics across periods."""
    periods_list = [p.strip() for p in periods.split(",")]
    asyncio.run(_compute_trends_async(location_id, periods_list))


@app.command()
def analytics_refresh(
    location_id: int | None = typer.Option(None, help="Specific location ID or all locations")
):
    """Run all analytics computations (aggregations, accuracy, trends)."""
    asyncio.run(_analytics_refresh_async(location_id))


async def _seed_data_async(days: int, locations_arg: str, no_refresh: bool):
    """Async implementation of seed data command."""
    start_time = datetime.utcnow()
    logger.info(
        "Starting data seeding",
        action="seed.run",
        status="started",
        days=days,
        locations_arg=locations_arg,
        no_refresh=no_refresh
    )

    async with AsyncSessionLocal() as session:
        location_repo = LocationRepository(session)
        ingestion_service = IngestionService(session)

        # Get target locations
        if locations_arg == "all":
            locations_list = await location_repo.get_all()
        else:
            location_ids = [int(x.strip()) for x in locations_arg.split(",")]
            locations_list = []
            for location_id in location_ids:
                location = await location_repo.get_by_id(location_id)
                if location:
                    locations_list.append(location)

        if not locations_list:
            logger.warning("No locations found to seed", action="seed.run", status="no_locations")
            return

        # Check if data already exists for the date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        total_inserted = 0
        skipped_count = 0

        for location in locations_list:
            logger.info(
                "Seeding data for location",
                action="seed.run",
                location_id=location.id,
                location_name=location.name
            )

            # Check for existing data (idempotent check)
            existing_obs = await ingestion_service.count_observations_in_range(
                location.id, start_date, end_date
            )

            if existing_obs > 0:
                logger.info(
                    "Existing data found, skipping location",
                    action="seed.run",
                    location_id=location.id,
                    existing_observations=existing_obs
                )
                skipped_count += 1
                continue

            # Generate hourly data for the past N days
            current_time = start_date
            location_inserts = 0

            while current_time <= end_date:
                # Create synthetic observation
                obs_data = await ingestion_service.create_synthetic_observation(
                    location.id, current_time
                )
                if obs_data:
                    location_inserts += 1

                # Create synthetic forecast (issued 6 hours ago, targeting this time)
                if current_time >= start_date + timedelta(hours=6):
                    forecast_issue_time = current_time - timedelta(hours=6)
                    forecast_data = await ingestion_service.create_synthetic_forecast(
                        location.id, forecast_issue_time, current_time
                    )
                    if forecast_data:
                        location_inserts += 1

                current_time += timedelta(hours=1)

            await session.commit()
            total_inserted += location_inserts
            logger.info(
                "Completed seeding for location",
                action="seed.run",
                location_id=location.id,
                records_inserted=location_inserts
            )

    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    # Trigger analytics refresh unless disabled
    if not no_refresh and not settings.no_refresh:
        logger.info(
            "Triggering analytics refresh after seeding",
            action="seed.run",
            status="triggering_refresh"
        )
        await _analytics_refresh_async(None)

    logger.info(
        "Data seeding completed",
        action="seed.run",
        status="success",
        total_locations=len(locations_list),
        total_inserted=total_inserted,
        skipped_locations=skipped_count,
        duration_ms=duration_ms,
        analytics_refreshed=not (no_refresh or settings.no_refresh)
    )


async def _compute_aggregations_async(location_id: int | None, days: int):
    """Async implementation of compute aggregations command."""
    logger.info(
        "Starting aggregations computation",
        action="compute.aggregations",
        location_id=location_id,
        days=days
    )

    async with AsyncSessionLocal() as session:
        computation_service = AnalyticsComputationService(session)

        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow() - timedelta(days=1)  # Exclude today

        result = await computation_service.compute_daily_aggregations(
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(
            "Aggregations computation completed",
            action="compute.aggregations",
            **result
        )


async def _compute_accuracy_async(location_id: int | None, days: int):
    """Async implementation of compute accuracy command."""
    logger.info(
        "Starting accuracy computation",
        action="compute.accuracy",
        location_id=location_id,
        days=days
    )

    async with AsyncSessionLocal() as session:
        computation_service = AnalyticsComputationService(session)

        start_time = datetime.utcnow() - timedelta(days=days)
        end_time = datetime.utcnow()

        result = await computation_service.compute_forecast_accuracy(
            location_id=location_id,
            start_time=start_time,
            end_time=end_time
        )

        logger.info(
            "Accuracy computation completed",
            action="compute.accuracy",
            **result
        )


async def _compute_trends_async(location_id: int | None, periods: list[str]):
    """Async implementation of compute trends command."""
    logger.info(
        "Starting trends computation",
        action="compute.trends",
        location_id=location_id,
        periods=periods
    )

    async with AsyncSessionLocal() as session:
        computation_service = AnalyticsComputationService(session)

        result = await computation_service.compute_trends(
            location_id=location_id,
            periods=periods
        )

        logger.info(
            "Trends computation completed",
            action="compute.trends",
            **result
        )


async def _analytics_refresh_async(location_id: int | None):
    """Async implementation of analytics refresh command."""
    logger.info(
        "Starting full analytics refresh",
        action="analytics.refresh",
        location_id=location_id
    )

    async with AsyncSessionLocal() as session:
        computation_service = AnalyticsComputationService(session)

        result = await computation_service.refresh_all_analytics(
            location_id=location_id
        )

        logger.info(
            "Full analytics refresh completed",
            action="analytics.refresh",
            **result
        )


if __name__ == "__main__":
    app()
