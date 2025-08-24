"""Management commands for WeatherAI backend."""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Optional

import structlog
import typer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.repositories import LocationRepository
from app.analytics.services.ingestion_service import IngestionService

logger = structlog.get_logger(__name__)

app = typer.Typer()


@app.command()
def seed_data(
    days: int = typer.Option(7, help="Number of days of data to seed"),
    locations: str = typer.Option("all", help="Location IDs (comma-separated) or 'all'")
):
    """Seed synthetic observation and forecast data for development."""
    asyncio.run(_seed_data_async(days, locations))


async def _seed_data_async(days: int, locations_arg: str):
    """Async implementation of seed data command."""
    start_time = datetime.utcnow()
    logger.info(
        "Starting data seeding",
        action="seed.run",
        status="started",
        days=days,
        locations_arg=locations_arg
    )
    
    async with SessionLocal() as session:
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
    logger.info(
        "Data seeding completed",
        action="seed.run",
        status="success",
        total_locations=len(locations_list),
        total_inserted=total_inserted,
        skipped_locations=skipped_count,
        duration_ms=duration_ms
    )


if __name__ == "__main__":
    app()