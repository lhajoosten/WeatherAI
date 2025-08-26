import logging
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.models import TrendCache

logger = logging.getLogger(__name__)


class TrendRepository:
    """Repository for TrendCache operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_or_update(
        self,
        location_id: int,
        metric: str,
        period: str,
        current_value: float | None,
        previous_value: float | None
    ) -> TrendCache:
        """Create or update a trend cache record (idempotent)."""
        # Calculate delta and percentage change
        delta = None
        pct_change = None

        if current_value is not None and previous_value is not None:
            delta = current_value - previous_value
            if previous_value != 0:
                pct_change = (delta / abs(previous_value)) * 100

        # Check if record exists
        stmt = select(TrendCache).where(
            and_(
                TrendCache.location_id == location_id,
                TrendCache.metric == metric,
                TrendCache.period == period
            )
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing record
            existing.current_value = current_value
            existing.previous_value = previous_value
            existing.delta = delta
            existing.pct_change = pct_change
            existing.generated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new record with error handling for FK violations
            try:
                trend = TrendCache(
                    location_id=location_id,
                    metric=metric,
                    period=period,
                    current_value=current_value,
                    previous_value=previous_value,
                    delta=delta,
                    pct_change=pct_change
                )
                self.session.add(trend)
                await self.session.commit()
                await self.session.refresh(trend)
                return trend
            except Exception as e:
                # Handle FK constraint errors gracefully
                await self.session.rollback()
                logger.warning(
                    "Failed to create trend cache record",
                    location_id=location_id,
                    metric=metric,
                    period=period,
                    error=str(e)
                )
                raise  # Re-raise to trigger upstream error handling

    async def get_by_location_and_metrics(
        self,
        location_id: int,
        period: str,
        metrics: list[str] | None = None
    ) -> list[TrendCache]:
        """Get trend records for a location and optional metrics filter."""
        stmt = select(TrendCache).where(
            and_(
                TrendCache.location_id == location_id,
                TrendCache.period == period
            )
        )

        if metrics:
            stmt = stmt.where(TrendCache.metric.in_(metrics))

        stmt = stmt.order_by(TrendCache.metric)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
