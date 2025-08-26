"""Repository for AstronomyDaily operations."""
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import AstronomyDaily

logger = logging.getLogger(__name__)


class AstronomyRepository:
    """Repository for AstronomyDaily operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        location_id: int,
        date: datetime,
        sunrise_utc: datetime | None = None,
        sunset_utc: datetime | None = None,
        daylight_minutes: int | None = None,
        moon_phase: float | None = None,
        civil_twilight_start_utc: datetime | None = None,
        civil_twilight_end_utc: datetime | None = None,
        generated_at: datetime | None = None
    ) -> AstronomyDaily:
        """Create a new astronomy record."""
        if generated_at is None:
            generated_at = datetime.utcnow()

        astronomy = AstronomyDaily(
            location_id=location_id,
            date=date,
            sunrise_utc=sunrise_utc,
            sunset_utc=sunset_utc,
            daylight_minutes=daylight_minutes,
            moon_phase=moon_phase,
            civil_twilight_start_utc=civil_twilight_start_utc,
            civil_twilight_end_utc=civil_twilight_end_utc,
            generated_at=generated_at
        )

        self.session.add(astronomy)
        await self.session.commit()
        await self.session.refresh(astronomy)

        return astronomy

    async def upsert(self, record: dict[str, Any]) -> AstronomyDaily:
        """Upsert astronomy record (update if exists, insert if not)."""
        try:
            # Check if record exists for this location and date
            stmt = select(AstronomyDaily).where(
                AstronomyDaily.location_id == record["location_id"],
                AstronomyDaily.date == record["date"]
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing record
                for key, value in record.items():
                    if key not in ["location_id", "date"]:
                        setattr(existing, key, value)
                existing.generated_at = datetime.utcnow()
                await self.session.commit()
                await self.session.refresh(existing)
                logger.info(f"Updated astronomy record for location {record['location_id']}, date {record['date']}")
                return existing
            else:
                # Create new record
                astronomy = AstronomyDaily(**record)
                self.session.add(astronomy)
                await self.session.commit()
                await self.session.refresh(astronomy)
                logger.info(f"Created astronomy record for location {record['location_id']}, date {record['date']}")
                return astronomy

        except Exception as e:
            logger.error(f"Error upserting astronomy record: {e}")
            await self.session.rollback()
            raise

    async def bulk_upsert(self, records: list[dict[str, Any]]) -> int:
        """Bulk upsert astronomy records."""
        if not records:
            return 0

        upserted_count = 0

        for record in records:
            try:
                await self.upsert(record)
                upserted_count += 1
            except Exception as e:
                logger.warning(f"Error upserting astronomy record: {e}")
                continue

        logger.info(f"Bulk upserted {upserted_count}/{len(records)} astronomy records")
        return upserted_count

    async def get_by_location_and_period(
        self,
        location_id: int,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> list[AstronomyDaily]:
        """Get astronomy data for a location within a date period."""
        stmt = select(AstronomyDaily).where(
            AstronomyDaily.location_id == location_id,
            AstronomyDaily.date >= start_date,
            AstronomyDaily.date <= end_date
        ).order_by(AstronomyDaily.date).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_for_location(self, location_id: int) -> AstronomyDaily | None:
        """Get the most recent astronomy record for a location."""
        stmt = select(AstronomyDaily).where(
            AstronomyDaily.location_id == location_id
        ).order_by(AstronomyDaily.date.desc()).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
