import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.db.models import AggregationDaily
from app.analytics.repositories.trend_repository import TrendRepository

logger = logging.getLogger(__name__)


class TrendService:
    """Service for computing trend metrics and rolling comparisons."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.trend_repo = TrendRepository(session)
    
    async def compute_trend_for_metric(
        self,
        location_id: int,
        metric: str,
        period: str,
        reference_date: Optional[datetime] = None
    ) -> Optional[Any]:
        """Compute trend for a specific metric and period.
        
        Args:
            location_id: Location to analyze
            metric: Metric name (e.g., 'avg_temp_c', 'total_precip_mm')
            period: Period string (e.g., '7d', '30d')
            reference_date: Date to calculate trend from (defaults to today)
        """
        if reference_date is None:
            reference_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        logger.info(f"Computing {period} trend for {metric} at location {location_id}")
        
        # Parse period
        if period.endswith('d'):
            days = int(period[:-1])
        else:
            logger.error(f"Unsupported period format: {period}")
            return None
        
        # Calculate date ranges
        current_period_start = reference_date - timedelta(days=days)
        current_period_end = reference_date
        
        previous_period_start = current_period_start - timedelta(days=days)
        previous_period_end = current_period_start
        
        # Get aggregations for current period
        current_value = await self._get_metric_average(
            location_id, metric, current_period_start, current_period_end
        )
        
        # Get aggregations for previous period
        previous_value = await self._get_metric_average(
            location_id, metric, previous_period_start, previous_period_end
        )
        
        # Store trend (idempotent)
        trend = await self.trend_repo.create_or_update(
            location_id=location_id,
            metric=metric,
            period=period,
            current_value=current_value,
            previous_value=previous_value
        )
        
        logger.info(f"Computed trend: {metric} {period} = {current_value} vs {previous_value} (Δ={trend.delta}, {trend.pct_change}%)")
        return trend
    
    async def _get_metric_average(
        self,
        location_id: int,
        metric: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[float]:
        """Get average value for a metric over a date range."""
        # Map metric names to database columns
        metric_column_map = {
            'avg_temp_c': AggregationDaily.avg_temp_c,
            'temp_min_c': AggregationDaily.temp_min_c,
            'temp_max_c': AggregationDaily.temp_max_c,
            'total_precip_mm': AggregationDaily.total_precip_mm,
            'max_wind_kph': AggregationDaily.max_wind_kph,
            'heating_degree_days': AggregationDaily.heating_degree_days,
            'cooling_degree_days': AggregationDaily.cooling_degree_days
        }
        
        if metric not in metric_column_map:
            logger.error(f"Unknown metric: {metric}")
            return None
        
        column = metric_column_map[metric]
        
        # For precipitation, use sum; for others, use average
        if metric == 'total_precip_mm':
            agg_func = func.sum(column)
        else:
            agg_func = func.avg(column)
        
        stmt = select(agg_func).where(
            AggregationDaily.location_id == location_id,
            AggregationDaily.date >= start_date,
            AggregationDaily.date < end_date,
            column.is_not(None)
        )
        
        result = await self.session.execute(stmt)
        value = result.scalar()
        
        return float(value) if value is not None else None
    
    async def compute_all_trends_for_location(
        self,
        location_id: int,
        periods: List[str] = None,
        metrics: List[str] = None
    ) -> List[Any]:
        """Compute all trend combinations for a location."""
        if periods is None:
            periods = ['7d', '30d']
        
        if metrics is None:
            metrics = ['avg_temp_c', 'total_precip_mm', 'max_wind_kph']
        
        logger.info(f"Computing {len(periods)} x {len(metrics)} trends for location {location_id}")
        
        trends = []
        for period in periods:
            for metric in metrics:
                trend = await self.compute_trend_for_metric(location_id, metric, period)
                if trend:
                    trends.append(trend)
        
        logger.info(f"Computed {len(trends)} trends")
        return trends