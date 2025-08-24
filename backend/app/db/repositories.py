from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import ForecastCache, LLMAudit, Location, User, UserProfile, UserPreferences


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

    async def update(self, location_id: int, user_id: int, **updates) -> Location | None:
        """Update location if it belongs to the user."""
        location = await self.get_by_id_and_user(location_id, user_id)
        if not location:
            return None
            
        for key, value in updates.items():
            if hasattr(location, key) and value is not None:
                setattr(location, key, value)
                
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def delete(self, location_id: int, user_id: int) -> bool:
        """Delete location if it belongs to the user."""
        location = await self.get_by_id_and_user(location_id, user_id)
        if not location:
            return False
            
        await self.session.delete(location)
        await self.session.commit()
        return True


class LocationGroupRepository:
    """Repository for LocationGroup operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, name: str, description: str | None = None):
        """Create a new location group for a user."""
        from app.db.models import LocationGroup
        
        group = LocationGroup(
            user_id=user_id,
            name=name,
            description=description
        )
        self.session.add(group)
        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def get_by_user_id(self, user_id: int):
        """Get all location groups for a user with their members."""
        from app.db.models import LocationGroup, LocationGroupMember, Location
        
        result = await self.session.execute(
            select(LocationGroup)
            .where(LocationGroup.user_id == user_id)
            .order_by(LocationGroup.created_at)
        )
        groups = result.scalars().all()
        
        # Load members for each group
        for group in groups:
            members_result = await self.session.execute(
                select(Location)
                .join(LocationGroupMember)
                .where(LocationGroupMember.group_id == group.id)
                .order_by(LocationGroupMember.added_at)
            )
            group.members = members_result.scalars().all()
            
        return groups

    async def get_by_id_and_user(self, group_id: int, user_id: int):
        """Get location group by ID if it belongs to the user."""
        from app.db.models import LocationGroup
        
        result = await self.session.execute(
            select(LocationGroup).where(
                LocationGroup.id == group_id,
                LocationGroup.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def add_member(self, group_id: int, location_id: int, user_id: int):
        """Add a location to a group if both belong to the user."""
        from app.db.models import LocationGroupMember
        
        # Verify group ownership
        group = await self.get_by_id_and_user(group_id, user_id)
        if not group:
            return None
            
        # Verify location ownership
        location_repo = LocationRepository(self.session)
        location = await location_repo.get_by_id_and_user(location_id, user_id)
        if not location:
            return None
            
        # Check if membership already exists
        existing_result = await self.session.execute(
            select(LocationGroupMember).where(
                LocationGroupMember.group_id == group_id,
                LocationGroupMember.location_id == location_id
            )
        )
        if existing_result.scalar_one_or_none():
            return None  # Already a member
            
        # Create membership
        member = LocationGroupMember(
            group_id=group_id,
            location_id=location_id
        )
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return member

    async def remove_member(self, group_id: int, location_id: int, user_id: int) -> bool:
        """Remove a location from a group if the group belongs to the user."""
        from app.db.models import LocationGroupMember
        
        # Verify group ownership
        group = await self.get_by_id_and_user(group_id, user_id)
        if not group:
            return False
            
        # Find and delete membership
        result = await self.session.execute(
            select(LocationGroupMember).where(
                LocationGroupMember.group_id == group_id,
                LocationGroupMember.location_id == location_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False
            
        await self.session.delete(member)
        await self.session.commit()
        return True

    async def delete(self, group_id: int, user_id: int) -> bool:
        """Delete a location group if it belongs to the user."""
        group = await self.get_by_id_and_user(group_id, user_id)
        if not group:
            return False
            
        await self.session.delete(group)
        await self.session.commit()
        return True


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


class UserProfileRepository:
    """Repository for UserProfile operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> UserProfile | None:
        """Get user profile by user ID."""
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(self, user_id: int, **kwargs) -> UserProfile:
        """Create or update user profile."""
        profile = await self.get_by_user_id(user_id)
        
        if profile:
            # Update existing profile
            for key, value in kwargs.items():
                if hasattr(profile, key) and value is not None:
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
        else:
            # Create new profile
            profile = UserProfile(user_id=user_id, **kwargs)
            self.session.add(profile)
        
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def update(self, user_id: int, **kwargs) -> UserProfile | None:
        """Update user profile fields."""
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return None
        
        for key, value in kwargs.items():
            if hasattr(profile, key) and value is not None:
                setattr(profile, key, value)
        
        profile.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(profile)
        return profile


class UserPreferencesRepository:
    """Repository for UserPreferences operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> UserPreferences | None:
        """Get user preferences by user ID."""
        result = await self.session.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(self, user_id: int, **kwargs) -> UserPreferences:
        """Create or update user preferences."""
        preferences = await self.get_by_user_id(user_id)
        
        if preferences:
            # Update existing preferences
            for key, value in kwargs.items():
                if hasattr(preferences, key) and value is not None:
                    setattr(preferences, key, value)
            preferences.updated_at = datetime.utcnow()
        else:
            # Create new preferences with defaults
            default_values = {
                'units_system': 'metric',
                'show_wind': True,
                'show_precip': True,
                'show_humidity': True,
            }
            default_values.update(kwargs)
            preferences = UserPreferences(user_id=user_id, **default_values)
            self.session.add(preferences)
        
        await self.session.commit()
        await self.session.refresh(preferences)
        return preferences

    async def update(self, user_id: int, **kwargs) -> UserPreferences | None:
        """Update user preferences fields."""
        preferences = await self.get_by_user_id(user_id)
        if not preferences:
            return None
        
        for key, value in kwargs.items():
            if hasattr(preferences, key) and value is not None:
                setattr(preferences, key, value)
        
        preferences.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(preferences)
        return preferences
