import asyncio
import logging
from datetime import datetime, timedelta

from app.application.analytics.accuracy_service import AccuracyService
from app.application.analytics.aggregation_service import AggregationService
from app.application.analytics.trend_service import TrendService
from app.core.config import settings
from app.infrastructure.db.database import get_db
from app.infrastructure.db import LocationRepository
from app.infrastructure.ingestion.orchestrator import IngestionOrchestrator

logger = logging.getLogger(__name__)


class AnalyticsScheduler:
    """Lightweight scheduler for analytics background tasks.

    Phase 1: Simple async loop scheduler.
    TODO: Replace with dedicated worker process (Celery/APScheduler) in production.
    """

    def __init__(self):
        self.running = False
        self._tasks = []

    async def start(self):
        """Start the analytics scheduler."""
        if self.running:
            logger.warning("Analytics scheduler is already running")
            return

        self.running = True
        logger.info("Starting analytics scheduler...")

        # Schedule tasks
        self._tasks = [
            asyncio.create_task(self._ingestion_cycle()),
            asyncio.create_task(self._aggregation_cycle()),
            asyncio.create_task(self._accuracy_cycle()),
            asyncio.create_task(self._trend_cycle())
        ]

        logger.info("Analytics scheduler started with 4 background tasks")

    async def stop(self):
        """Stop the analytics scheduler."""
        if not self.running:
            return

        logger.info("Stopping analytics scheduler...")
        self.running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        logger.info("Analytics scheduler stopped")

    async def _ingestion_cycle(self):
        """Periodic ingestion using multi-provider orchestrator."""
        logger.info("Starting ingestion cycle")

        while self.running:
            try:
                await self._run_ingestion_cycle()
                # Use configured interval (default 2 hours)
                interval_seconds = settings.ingest_interval_minutes * 60
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in ingestion cycle: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _aggregation_cycle(self):
        """Periodic computation of daily aggregations."""
        logger.info("Starting aggregation cycle")

        while self.running:
            try:
                await self._run_daily_aggregations()
                # Run every 4 hours
                await asyncio.sleep(4 * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in aggregation cycle: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _accuracy_cycle(self):
        """Periodic computation of forecast accuracy."""
        logger.info("Starting accuracy cycle")

        while self.running:
            try:
                await self._run_accuracy_cycle()
                # Run every 8 hours
                await asyncio.sleep(8 * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in accuracy cycle: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _trend_cycle(self):
        """Periodic computation of trend analysis."""
        logger.info("Starting trend cycle")

        while self.running:
            try:
                await self._run_trend_refresh()
                # Run every 2 hours
                await asyncio.sleep(2 * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in trend cycle: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _run_ingestion_cycle(self):
        """Run ingestion for all locations using multi-provider orchestrator."""
        logger.info("Running multi-provider ingestion cycle...")

        # TODO: Replace direct get_db() session acquisition with repository-level
        # orchestration abstraction in future phases (Phase 2+)
        async for session in get_db():
            try:
                # Use new orchestrator instead of mock ingestion service
                orchestrator = IngestionOrchestrator(session)

                # TODO: Get list of active locations from database
                # For now, use demo locations 1-3, limited by MAX_LOCATIONS_PER_INGEST
                demo_location_ids = [1, 2, 3]
                limited_location_ids = demo_location_ids[:settings.max_locations_per_ingest]

                # Run orchestrated ingestion cycle
                results = await orchestrator.run_ingestion_cycle(limited_location_ids)

                logger.info(f"Ingestion cycle completed: {results['successful_locations']}/{results['total_locations']} locations successful, "
                           f"{results['tasks_completed']} tasks completed, {results['tasks_failed']} tasks failed")

                if results['errors']:
                    logger.warning(f"Ingestion errors: {results['errors']}")

                break

            except Exception as e:
                logger.exception(f"Error in ingestion cycle: {e}")

    async def _run_daily_aggregations(self):
        """Run daily aggregations for recent dates."""
        logger.info("Running daily aggregations...")

        async for session in get_db():
            try:
                aggregation_service = AggregationService(session)

                # Compute aggregations for last 3 days
                end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = end_date - timedelta(days=3)

                demo_location_ids = [1, 2, 3]

                for location_id in demo_location_ids:
                    try:
                        aggregations = await aggregation_service.compute_aggregations_for_period(
                            location_id=location_id,
                            start_date=start_date,
                            end_date=end_date
                        )
                        logger.info(f"Computed {len(aggregations)} aggregations for location {location_id}")

                    except Exception as e:
                        logger.error(f"Failed aggregations for location {location_id}: {e}")

                logger.info("Daily aggregations completed")
                break

            except Exception as e:
                logger.exception(f"Error in aggregation cycle: {e}")

    async def _run_accuracy_cycle(self):
        """Run accuracy computations for recent forecasts."""
        logger.info("Running accuracy cycle...")

        async for session in get_db():
            try:
                accuracy_service = AccuracyService(session)

                # Compute accuracy for last 7 days
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=7)

                demo_location_ids = [1, 2, 3]

                for location_id in demo_location_ids:
                    try:
                        accuracy_records = await accuracy_service.compute_accuracy_for_period(
                            location_id=location_id,
                            start_time=start_time,
                            end_time=end_time,
                            forecast_lead_hours=24
                        )
                        logger.info(f"Computed {len(accuracy_records)} accuracy records for location {location_id}")

                    except Exception as e:
                        logger.error(f"Failed accuracy computation for location {location_id}: {e}")

                logger.info("Accuracy cycle completed")
                break

            except Exception as e:
                logger.exception(f"Error in accuracy cycle: {e}")

    async def _run_trend_refresh(self):
        """Run trend computations for all locations."""
        logger.info("Running trend refresh...", extra={"action":"trend.compute","status":"started"})

        async for session in get_db():
            try:
                trend_service = TrendService(session)
                location_repo = LocationRepository(session)

                # Retrieve dynamic location IDs to avoid FK violations
                locations = await location_repo.get_all()
                if not locations:
                    logger.info("No locations found, skipping trend refresh", extra={"action":"trend.compute", "status":"no_locations"})
                    break

                location_ids = [loc.id for loc in locations]
                logger.info(f"Computing trends for {len(location_ids)} locations", extra={"action":"trend.compute", "location_count":len(location_ids)})

                total_trends = 0
                failed_locations = 0

                for location in locations:
                    try:
                        trends = await trend_service.compute_all_trends_for_location(
                            location_id=location.id,
                            periods=['7d', '30d'],
                            metrics=['avg_temp_c', 'total_precip_mm', 'max_wind_kph']
                        )
                        total_trends += len(trends)
                        logger.info(
                            "Computed trends for location",
                            extra={
                                "action": "trend.compute",
                                "location_id": location.id,
                                "location_name": location.name,
                                "trends_computed": len(trends)
                            }
                        )

                    except Exception as e:
                        failed_locations += 1
                        logger.warning(
                            "Failed trend computation for location",
                            extra={
                                "action": "trend.compute",
                                "status": "failed",
                                "location_id": location.id,
                                "location_name": location.name,
                                "error": str(e)
                            }
                        )

                logger.info(
                    "Trend refresh completed",
                    extra={
                        "action": "trend.compute",
                        "status": "success",
                        "total_trends": total_trends,
                        "total_locations": len(location_ids),
                        "failed_locations": failed_locations
                    }
                )
                break

            except Exception as e:
                logger.exception(f"Error in trend cycle: {e}", extra={"action":"trend.compute", "status":"error"})


# Global scheduler instance
analytics_scheduler = AnalyticsScheduler()
