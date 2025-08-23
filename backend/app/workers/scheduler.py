import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from app.db.database import get_db
from app.analytics.services.ingestion_service import IngestionService
from app.analytics.services.aggregation_service import AggregationService
from app.analytics.services.accuracy_service import AccuracyService
from app.analytics.services.trend_service import TrendService

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
        """Periodic ingestion of mock data for testing."""
        logger.info("Starting ingestion cycle")
        
        while self.running:
            try:
                await self._run_ingestion_cycle()
                # Run every 6 hours
                await asyncio.sleep(6 * 3600)
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
        """Run ingestion for all locations with mock data."""
        logger.info("Running ingestion cycle...")
        
        async for session in get_db():
            try:
                ingestion_service = IngestionService(session)
                
                # TODO: Get list of active locations from database
                # For now, generate data for demo locations 1-3
                demo_location_ids = [1, 2, 3]
                
                for location_id in demo_location_ids:
                    try:
                        # Generate mock observations (last 6 hours)
                        await ingestion_service.ingest_mock_observations(location_id, hours_back=6)
                        
                        # Generate mock forecasts (next 24 hours)
                        await ingestion_service.ingest_mock_forecasts(location_id, hours_ahead=24)
                        
                        logger.info(f"Completed ingestion for location {location_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed ingestion for location {location_id}: {e}")
                
                logger.info("Ingestion cycle completed")
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
        logger.info("Running trend refresh...")
        
        async for session in get_db():
            try:
                trend_service = TrendService(session)
                
                demo_location_ids = [1, 2, 3]
                
                for location_id in demo_location_ids:
                    try:
                        trends = await trend_service.compute_all_trends_for_location(
                            location_id=location_id,
                            periods=['7d', '30d'],
                            metrics=['avg_temp_c', 'total_precip_mm', 'max_wind_kph']
                        )
                        logger.info(f"Computed {len(trends)} trends for location {location_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed trend computation for location {location_id}: {e}")
                
                logger.info("Trend refresh completed")
                break
                
            except Exception as e:
                logger.exception(f"Error in trend cycle: {e}")


# Global scheduler instance
analytics_scheduler = AnalyticsScheduler()