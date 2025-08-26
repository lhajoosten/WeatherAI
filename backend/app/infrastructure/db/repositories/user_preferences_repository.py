"""User preferences repository."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.models import UserPreferences


class UserPreferencesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> UserPreferences | None:
        result = await self.session.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_or_update(self, user_id: int, **kwargs) -> UserPreferences:
        prefs = await self.get_by_user_id(user_id)
        if prefs:
            for k, v in kwargs.items():
                setattr(prefs, k, v)
        else:
            prefs = UserPreferences(user_id=user_id, **kwargs)
            self.session.add(prefs)
        await self.session.commit()
        await self.session.refresh(prefs)
        return prefs

    async def update(self, user_id: int, **kwargs) -> UserPreferences | None:
        prefs = await self.get_by_user_id(user_id)
        if not prefs:
            return None
        for k, v in kwargs.items():
            setattr(prefs, k, v)
        await self.session.commit()
        await self.session.refresh(prefs)
        return prefs

__all__ = ["UserPreferencesRepository"]
