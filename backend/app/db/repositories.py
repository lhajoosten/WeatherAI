from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import ForecastCache, LLMAudit, Location, User


class UserRepository:
    """Repository for User operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, email: str, password_hash: str, timezone: str = "UTC") -> User:
        """Create a new user."""
        user = User(
            email=email,
            password_hash=password_hash,
            timezone=timezone
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


class LocationRepository:
    """Repository for Location operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, name: str, lat: float, lon: float, timezone: str | None = None) -> Location:
        """Create a new location for a user."""
        location = Location(
            user_id=user_id,
            name=name,
            lat=lat,
            lon=lon,
            timezone=timezone
        )
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def get_by_user_id(self, user_id: int) -> list[Location]:
        """Get all locations for a user."""
        result = await self.session.execute(
            select(Location).where(Location.user_id == user_id).order_by(Location.created_at)
        )
        return result.scalars().all()

    async def get_by_id(self, location_id: int) -> Location | None:
        """Get location by ID."""
        result = await self.session.execute(
            select(Location).where(Location.id == location_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_user(self, location_id: int, user_id: int) -> Location | None:
        """Get location by ID if it belongs to the user."""
        result = await self.session.execute(
            select(Location).where(
                Location.id == location_id,
                Location.user_id == user_id
            )
        )
        return result.scalar_one_or_none()


class ForecastRepository:
    """Repository for ForecastCache operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, location_id: int, source: str, payload_json: str, expires_at: datetime) -> ForecastCache:
        """Create new forecast cache entry."""
        forecast = ForecastCache(
            location_id=location_id,
            source=source,
            payload_json=payload_json,
            expires_at=expires_at
        )
        self.session.add(forecast)
        await self.session.commit()
        await self.session.refresh(forecast)
        return forecast

    async def get_latest_for_location(self, location_id: int, source: str = "mock") -> ForecastCache | None:
        """Get the latest non-expired forecast for a location."""
        result = await self.session.execute(
            select(ForecastCache)
            .where(
                ForecastCache.location_id == location_id,
                ForecastCache.source == source,
                ForecastCache.expires_at > datetime.utcnow()
            )
            .order_by(ForecastCache.fetched_at.desc())
        )
        return result.scalar_one_or_none()


class LLMAuditRepository:
    """Repository for LLMAudit operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self,
        user_id: int | None,
        endpoint: str,
        model: str,
        prompt_summary: str,
        tokens_in: int,
        tokens_out: int,
        cost: float | None = None
    ) -> LLMAudit:
        """Record an LLM API call for auditing."""
        audit = LLMAudit(
            user_id=user_id,
            endpoint=endpoint,
            model=model,
            prompt_summary=prompt_summary[:200],  # Ensure truncation
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost
        )
        self.session.add(audit)
        await self.session.commit()
        await self.session.refresh(audit)
        return audit

    async def get_user_usage_today(self, user_id: int) -> list[LLMAudit]:
        """Get today's LLM usage for a user (for quota tracking)."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(LLMAudit)
            .where(
                LLMAudit.user_id == user_id,
                LLMAudit.created_at >= today_start
            )
            .order_by(LLMAudit.created_at.desc())
        )
        return result.scalars().all()
