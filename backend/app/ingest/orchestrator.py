"""Ingestion orchestrator coordinating multi-provider data ingestion."""
import asyncio
import logging
import random
from datetime import date, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.repositories.air_quality_repository import AirQualityRepository
from app.analytics.repositories.astronomy_repository import AstronomyRepository
from app.analytics.repositories.forecast_repository import ForecastRepository
from app.analytics.repositories.observation_repository import ObservationRepository
from app.analytics.repositories.provider_run_repository import ProviderRunRepository
from app.core.config import settings
from app.core.datetime_utils import truncate_error_message
from app.ingest.astronomy_service import AstronomyComputationService
from app.ingest.providers.openmeteo_air_quality import OpenMeteoAirQualityProvider
from app.ingest.providers.openmeteo_forecast import OpenMeteoForecastProvider
from app.ingest.providers.openmeteo_observation import OpenMeteoObservationProvider

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """Orchestrates sequential data ingestion tasks across multiple providers."""

    def __init__(self, session: AsyncSession):
        self.session = session

        # Initialize repositories
        self.provider_run_repo = ProviderRunRepository(session)
        self.forecast_repo = ForecastRepository(session)
        self.observation_repo = ObservationRepository(session)
        self.air_quality_repo = AirQualityRepository(session)
        self.astronomy_repo = AstronomyRepository(session)

        # Initialize providers
        self.forecast_provider = OpenMeteoForecastProvider()
        self.observation_provider = OpenMeteoObservationProvider()
        self.air_quality_provider = OpenMeteoAirQualityProvider()
        self.astronomy_service = AstronomyComputationService()

    async def run_ingestion_cycle(self, location_ids: list[int]) -> dict[str, Any]:
        """Run complete ingestion cycle for given locations."""

        # Check if ingestion is disabled in development
        if settings.app_env == "development" and settings.disable_ingest_in_dev:
            logger.info("Ingestion disabled in development (DISABLE_INGEST_IN_DEV=true)")
            return {
                "total_locations": len(location_ids),
                "successful_locations": 0,
                "failed_locations": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "errors": [],
                "skipped": True,
                "reason": "Disabled in development"
            }

        logger.info(f"Starting ingestion cycle for {len(location_ids)} locations")

        results = {
            "total_locations": len(location_ids),
            "successful_locations": 0,
            "failed_locations": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "no_data_tasks": 0,
            "errors": []
        }

        for i, location_id in enumerate(location_ids):
            try:
                # Add jitter between location processes to avoid burst traffic
                if i > 0:  # Don't wait before first location
                    jitter_seconds = random.uniform(0, 2.0)
                    logger.debug(f"Adding {jitter_seconds:.2f}s jitter before location {location_id}")
                    await asyncio.sleep(jitter_seconds)

                # Get location details (would normally query database)
                # For now, using mock coordinates - in real implementation, fetch from locations table
                location_results = await self._ingest_location(location_id, 40.7128, -74.0060)  # NYC coords as example

                results["successful_locations"] += 1
                results["tasks_completed"] += location_results["tasks_completed"]
                results["tasks_failed"] += location_results["tasks_failed"]
                results["no_data_tasks"] += location_results["no_data_tasks"]

                if location_results["errors"]:
                    results["errors"].extend(location_results["errors"])

            except Exception as e:
                logger.error(f"Failed to ingest location {location_id}: {e}")
                results["failed_locations"] += 1
                results["errors"].append(f"Location {location_id}: {truncate_error_message(str(e))}")

        logger.info(f"Ingestion cycle completed: {results['successful_locations']}/{results['total_locations']} locations successful, {results['tasks_completed']} tasks completed, {results['tasks_failed']} failed, {results['no_data_tasks']} no data")
        return results

    async def _ingest_location(self, location_id: int, lat: float, lon: float) -> dict[str, Any]:
        """Ingest all data types for a single location."""
        logger.info(f"Ingesting data for location {location_id} at {lat}, {lon}")

        results = {
            "location_id": location_id,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "no_data_tasks": 0,
            "errors": []
        }

        tasks = [
            ("forecast", self._fetch_forecast),
            ("observation", self._fetch_observations),
            ("air_quality", self._fetch_air_quality),
            ("astronomy", self._compute_astronomy)
        ]

        for task_name, task_func in tasks:
            try:
                task_result = await task_func(location_id, lat, lon)
                if task_result == "NO_DATA":
                    results["no_data_tasks"] += 1
                    logger.info(f"No data available for {task_name} for location {location_id}")
                else:
                    results["tasks_completed"] += 1
                    logger.info(f"Completed {task_name} for location {location_id}")
            except Exception as e:
                logger.error(f"Failed {task_name} for location {location_id}: {e}")
                results["tasks_failed"] += 1
                results["errors"].append(f"{task_name}: {truncate_error_message(str(e))}")

        return results

    async def _fetch_forecast(self, location_id: int, lat: float, lon: float):
        """Fetch and store forecast data."""
        provider_run = await self.provider_run_repo.create(
            provider=self.forecast_provider.provider_name,
            run_type="forecast",
            location_id=location_id
        )

        try:
            # Fetch forecast data
            forecast_records = await self.forecast_provider.fetch_forecast(location_id, lat, lon)

            # Store forecast data
            records_ingested = await self.forecast_repo.bulk_upsert(forecast_records)

            # Update provider run status
            await self.provider_run_repo.update_status(
                run_id=provider_run.id,
                status="SUCCESS",
                records_ingested=records_ingested
            )

        except Exception as e:
            await self.provider_run_repo.update_status(
                run_id=provider_run.id,
                status="FAILED",
                error_message=truncate_error_message(str(e))
            )
            raise

    async def _fetch_observations(self, location_id: int, lat: float, lon: float):
        """Fetch and store observation data."""
        provider_run = await self.provider_run_repo.create(
            provider=self.observation_provider.provider_name,
            run_type="observation",
            location_id=location_id
        )

        try:
            # Fetch observation data (last 6 hours)
            observation_records = await self.observation_provider.fetch_observations(location_id, lat, lon, hours_back=6)

            # Store observation data
            records_ingested = await self.observation_repo.bulk_upsert(observation_records)

            # Update provider run status
            await self.provider_run_repo.update_status(
                run_id=provider_run.id,
                status="SUCCESS",
                records_ingested=records_ingested
            )

        except Exception as e:
            await self.provider_run_repo.update_status(
                run_id=provider_run.id,
                status="FAILED",
                error_message=truncate_error_message(str(e))
            )
            raise

    async def _fetch_air_quality(self, location_id: int, lat: float, lon: float):
        """Fetch and store air quality data."""
        provider_run = await self.provider_run_repo.create(
            provider=self.air_quality_provider.provider_name,
            run_type="air_quality",
            location_id=location_id
        )

        try:
            # Fetch air quality data (last 24 hours)
            air_quality_records = await self.air_quality_provider.fetch_air_quality(location_id, lat, lon, hours_back=24)

            # Check if we got no data (empty list means 404 was handled gracefully)
            if not air_quality_records:
                # Update provider run status as NO_DATA
                await self.provider_run_repo.update_status(
                    run_id=provider_run.id,
                    status="NO_DATA",
                    records_ingested=0
                )
                return "NO_DATA"

            # Store air quality data
            records_ingested = await self.air_quality_repo.bulk_upsert(air_quality_records)

            # Update provider run status
            await self.provider_run_repo.update_status(
                run_id=provider_run.id,
                status="SUCCESS",
                records_ingested=records_ingested
            )

        except Exception as e:
            await self.provider_run_repo.update_status(
                run_id=provider_run.id,
                status="FAILED",
                error_message=truncate_error_message(str(e))
            )
            raise

    async def _compute_astronomy(self, location_id: int, lat: float, lon: float):
        """Compute and store astronomy data."""
        provider_run = await self.provider_run_repo.create(
            provider="astral",
            run_type="astronomy",
            location_id=location_id
        )

        try:
            # Compute astronomy for today and next few days
            today = date.today()
            astronomy_records = []

            for days_offset in range(7):  # Compute for next 7 days
                target_date = today + timedelta(days=days_offset)
                astronomy_data = self.astronomy_service.compute_astronomy_daily(location_id, lat, lon, target_date)
                astronomy_records.append(astronomy_data)

            # Store astronomy data
            records_ingested = await self.astronomy_repo.bulk_upsert(astronomy_records)

            # Update provider run status
            await self.provider_run_repo.update_status(
                run_id=provider_run.id,
                status="SUCCESS",
                records_ingested=records_ingested
            )

        except Exception as e:
            await self.provider_run_repo.update_status(
                run_id=provider_run.id,
                status="FAILED",
                error_message=truncate_error_message(str(e))
            )
            raise
