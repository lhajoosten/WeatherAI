import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import ObservationHourly

logger = logging.getLogger(__name__)


class ObservationRepository:
    """Repository for ObservationHourly operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        location_id: int,
        observed_at: datetime,
        temp_c: float | None = None,
        wind_kph: float | None = None,
        precip_mm: float | None = None,
        humidity_pct: float | None = None,
        condition_code: str | None = None,
        source: str = "mock",
        raw_json: str | None = None
    ) -> ObservationHourly:
        """Create a new observation record."""
        observation = ObservationHourly(
            location_id=location_id,
            observed_at=observed_at,
            temp_c=temp_c,
            wind_kph=wind_kph,
            precip_mm=precip_mm,
            humidity_pct=humidity_pct,
            condition_code=condition_code,
            source=source,
            raw_json=raw_json
        )
        self.session.add(observation)
        await self.session.commit()
        await self.session.refresh(observation)
        return observation

    async def get_by_location_and_period(
        self,
        location_id: int,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> list[ObservationHourly]:
        """Get observations for a location within a time period."""
        stmt = (
            select(ObservationHourly)
            .where(ObservationHourly.location_id == location_id)
            .where(ObservationHourly.observed_at >= start_time)
            .where(ObservationHourly.observed_at <= end_time)
            .order_by(ObservationHourly.observed_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_upsert(self, records: list[dict[str, Any]]) -> int:
        """Bulk upsert observation records with deduplication by (location_id, observed_at, source)."""
        if not records:
            return 0

        upserted_count = 0

        for record in records:
            try:
                # Check if record exists with same location, time, and source
                stmt = select(ObservationHourly).where(
                    ObservationHourly.location_id == record["location_id"],
                    ObservationHourly.observed_at == record["observed_at"],
                    ObservationHourly.source == record["source"]
                )
                result = await self.session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update existing record (prefer direct provider readings over METAR for overlap)
                    for key, value in record.items():
                        if key not in ["location_id", "observed_at", "source"]:
                            # Only update if new value is not None or existing is None
                            if value is not None or getattr(existing, key) is None:
                                setattr(existing, key, value)
                else:
                    # Create new record
                    new_record = ObservationHourly(**record)
                    self.session.add(new_record)

                upserted_count += 1

            except Exception as e:
                logger.warning(f"Error upserting observation record: {e}")
                continue

        await self.session.commit()
        logger.info(f"Bulk upserted {upserted_count}/{len(records)} observation records")
        return upserted_count

    async def count_by_date_range(
        self, location_id: int, start_date: datetime, end_date: datetime
    ) -> int:
        """Count observations in a date range for idempotent seeding."""
        from sqlalchemy import func

        stmt = select(func.count(ObservationHourly.id)).where(
            ObservationHourly.location_id == location_id,
            ObservationHourly.observed_at >= start_date,
            ObservationHourly.observed_at <= end_date
        )

        result = await self.session.execute(stmt)
        return result.scalar() or 0
