"""User profile repository."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.models import UserProfile


class UserProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> UserProfile | None:
        result = await self.session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_or_update(self, user_id: int, **kwargs) -> UserProfile:
        profile = await self.get_by_user_id(user_id)
        if profile:
            for k, v in kwargs.items():
                setattr(profile, k, v)
        else:
            profile = UserProfile(user_id=user_id, **kwargs)
            self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def update(self, user_id: int, **kwargs) -> UserProfile | None:
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return None
        for k, v in kwargs.items():
            setattr(profile, k, v)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

__all__ = ["UserProfileRepository"]
