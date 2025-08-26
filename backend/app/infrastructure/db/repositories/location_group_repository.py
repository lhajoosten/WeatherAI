"""Location group repository."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.infrastructure.db.models import LocationGroup, LocationGroupMember


class LocationGroupRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, name: str, description: str | None = None) -> LocationGroup:
        group = LocationGroup(user_id=user_id, name=name, description=description)
        self.session.add(group)
        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def get_by_user_id(self, user_id: int) -> list[LocationGroup]:
        result = await self.session.execute(select(LocationGroup).where(LocationGroup.user_id == user_id))
        return list(result.scalars().all())

    async def get_by_id_and_user(self, group_id: int, user_id: int) -> LocationGroup | None:
        result = await self.session.execute(select(LocationGroup).where(LocationGroup.id == group_id, LocationGroup.user_id == user_id))
        return result.scalar_one_or_none()

    async def add_member(self, group_id: int, location_id: int, user_id: int) -> bool:
        group = await self.get_by_id_and_user(group_id, user_id)
        if not group:
            return False
        existing = await self.session.execute(
            select(LocationGroupMember).where(LocationGroupMember.group_id == group_id, LocationGroupMember.location_id == location_id)
        )
        if existing.scalar_one_or_none():
            return True  # idempotent
        member = LocationGroupMember(group_id=group_id, location_id=location_id)
        self.session.add(member)
        await self.session.commit()
        return True

    async def remove_member(self, group_id: int, location_id: int, user_id: int) -> bool:
        group = await self.get_by_id_and_user(group_id, user_id)
        if not group:
            return False
        await self.session.execute(
            delete(LocationGroupMember).where(LocationGroupMember.group_id == group_id, LocationGroupMember.location_id == location_id)
        )
        await self.session.commit()
        return True

    async def delete(self, group_id: int, user_id: int) -> bool:
        group = await self.get_by_id_and_user(group_id, user_id)
        if not group:
            return False
        await self.session.delete(group)
        await self.session.commit()
        return True

__all__ = ["LocationGroupRepository"]
