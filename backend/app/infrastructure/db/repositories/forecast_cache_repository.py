"""Forecast cache repository (legacy simple cache)."""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.models import ForecastCache


class ForecastCacheRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, location_id: int, source: str, payload_json: str, expires_at: datetime) -> ForecastCache:
        cache = ForecastCache(location_id=location_id, source=source, payload_json=payload_json, expires_at=expires_at)
        self.session.add(cache)
        await self.session.commit()
        await self.session.refresh(cache)
        return cache

    async def get_latest_for_location(self, location_id: int, source: str = "mock") -> ForecastCache | None:
        stmt = (
            select(ForecastCache)
            .where(ForecastCache.location_id == location_id, ForecastCache.source == source)
            .order_by(ForecastCache.fetched_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

__all__ = ["ForecastCacheRepository"]
