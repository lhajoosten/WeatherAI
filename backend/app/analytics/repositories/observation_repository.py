from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import ObservationHourly


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
