"""Location repository."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.models import Location


class LocationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, name: str, lat: float, lon: float, timezone: str | None = None) -> Location:
        location = Location(user_id=user_id, name=name, lat=lat, lon=lon, timezone=timezone)
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def get_all(self) -> list[Location]:
        result = await self.session.execute(select(Location).order_by(Location.created_at))
        return list(result.scalars().all())

    async def get_by_user_id(self, user_id: int) -> list[Location]:
        result = await self.session.execute(select(Location).where(Location.user_id == user_id).order_by(Location.created_at))
        return list(result.scalars().all())

    async def get_by_id(self, location_id: int) -> Location | None:
        result = await self.session.execute(select(Location).where(Location.id == location_id))
        return result.scalar_one_or_none()

__all__ = ["LocationRepository"]
