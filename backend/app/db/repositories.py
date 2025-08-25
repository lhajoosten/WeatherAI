from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import (
    ForecastCache,
    LLMAudit,
    Location,
    RagDocument,
    RagDocumentChunk,
    User,
    UserPreferences,
    UserProfile,
)


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

    async def get_all(self) -> list[Location]:
        """Return all locations (ordered by creation)."""
        result = await self.session.execute(
            select(Location).order_by(Location.created_at)
        )
        return result.scalars().all()

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
        from sqlalchemy.exc import IntegrityError

        from app.db.models import (
            AggregationDaily,
            AirQualityHourly,
            AstronomyDaily,
            ForecastAccuracy,
            ForecastCache,
            ForecastHourly,
            LocationGroupMember,
            ObservationHourly,
            ProviderRun,
            TrendCache,
        )

        location = await self.get_by_id_and_user(location_id, user_id)
        if not location:
            return False

        try:
            # Try direct deletion first (in case FK constraints have CASCADE)
            await self.session.delete(location)
            await self.session.commit()
            return True
        except IntegrityError:
            # Rollback and perform manual cascade deletion
            await self.session.rollback()

            # Delete related records in dependency order
            # 1. Delete group memberships
            await self.session.execute(
                LocationGroupMember.__table__.delete().where(
                    LocationGroupMember.location_id == location_id
                )
            )

            # 2. Delete provider runs
            await self.session.execute(
                ProviderRun.__table__.delete().where(
                    ProviderRun.location_id == location_id
                )
            )

            # 3. Delete cached data
            for model in [ForecastCache, ObservationHourly, ForecastHourly,
                         AggregationDaily, ForecastAccuracy, TrendCache,
                         AirQualityHourly, AstronomyDaily]:
                await self.session.execute(
                    model.__table__.delete().where(
                        model.location_id == location_id
                    )
                )

            # 4. Finally delete the location
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
        from sqlalchemy.orm import selectinload

        from app.db.models import LocationGroup, LocationGroupMember

        result = await self.session.execute(
            select(LocationGroup)
            .options(selectinload(LocationGroup.members).selectinload(LocationGroupMember.location))
            .where(LocationGroup.user_id == user_id)
            .order_by(LocationGroup.created_at)
        )
        groups = result.scalars().all()

        return groups

    async def get_by_id_and_user(self, group_id: int, user_id: int):
        """Get location group by ID if it belongs to the user, with members loaded."""
        from sqlalchemy.orm import selectinload

        from app.db.models import LocationGroup, LocationGroupMember

        result = await self.session.execute(
            select(LocationGroup)
            .options(selectinload(LocationGroup.members).selectinload(LocationGroupMember.location))
            .where(
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

    async def bulk_update_members(self, group_id: int, user_id: int, add_location_ids: list[int], remove_location_ids: list[int]):
        """Bulk add/remove locations from a group."""
        import logging

        from sqlalchemy.orm import selectinload

        from app.db.models import LocationGroup, LocationGroupMember

        logger = logging.getLogger(__name__)

        # Verify group ownership
        group = await self.get_by_id_and_user(group_id, user_id)
        if not group:
            return None

        # Verify all locations belong to the user
        location_repo = LocationRepository(self.session)
        all_location_ids = set(add_location_ids + remove_location_ids)
        for location_id in all_location_ids:
            location = await location_repo.get_by_id_and_user(location_id, user_id)
            if not location:
                logger.warning(f"Location {location_id} not found or not owned by user {user_id}")
                continue  # Skip invalid locations rather than failing completely

        # Remove members (idempotent - ignore if not present)
        if remove_location_ids:
            result = await self.session.execute(
                select(LocationGroupMember).where(
                    LocationGroupMember.group_id == group_id,
                    LocationGroupMember.location_id.in_(remove_location_ids)
                )
            )
            members_to_remove = result.scalars().all()
            for member in members_to_remove:
                await self.session.delete(member)

        # Add members (idempotent - ignore if already present)
        if add_location_ids:
            # Get existing memberships to avoid duplicates
            existing_result = await self.session.execute(
                select(LocationGroupMember.location_id).where(
                    LocationGroupMember.group_id == group_id,
                    LocationGroupMember.location_id.in_(add_location_ids)
                )
            )
            existing_location_ids = {row[0] for row in existing_result.fetchall()}

            # Only add locations that aren't already members
            new_location_ids = [lid for lid in add_location_ids if lid not in existing_location_ids]
            for location_id in new_location_ids:
                member = LocationGroupMember(
                    group_id=group_id,
                    location_id=location_id
                )
                self.session.add(member)

        await self.session.commit()

        # Return updated group with eager-loaded members
        result = await self.session.execute(
            select(LocationGroup)
            .options(selectinload(LocationGroup.members).selectinload(LocationGroupMember.location))
            .where(LocationGroup.id == group_id)
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
        cost: float | None = None,
        has_air_quality: bool = False,
        has_astronomy: bool = False
    ) -> LLMAudit:
        """Record an LLM API call for auditing."""
        try:
            audit = LLMAudit(
                user_id=user_id,
                endpoint=endpoint,
                model=model,
                prompt_summary=prompt_summary[:200],  # Ensure truncation
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost=cost,
                has_air_quality=has_air_quality,
                has_astronomy=has_astronomy
            )
            self.session.add(audit)
            await self.session.commit()
            await self.session.refresh(audit)
            return audit
        except Exception as e:
            # Handle column mismatch gracefully (should not happen after migrations)
            await self.session.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to create LLM audit record for user {user_id}, endpoint {endpoint}: {e}"
            )
            # Don't re-raise - audit failures should not crash requests
            # Return a dummy audit record for backward compatibility
            return LLMAudit(
                id=0,
                user_id=user_id,
                endpoint=endpoint,
                model=model,
                prompt_summary=prompt_summary[:200],
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost=cost,
                has_air_quality=has_air_quality,
                has_astronomy=has_astronomy
            )

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


class RagDocumentRepository:
    """Repository for RAG document operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(self, source_id: str) -> RagDocument:
        """Create a new RAG document."""
        document = RagDocument(source_id=source_id)
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_by_source_id(self, source_id: str) -> RagDocument | None:
        """Get document by source ID."""
        result = await self.session.execute(
            select(RagDocument).where(RagDocument.source_id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, document_id: UUID) -> RagDocument | None:
        """Get document by ID."""
        result = await self.session.execute(
            select(RagDocument).where(RagDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def bulk_insert_chunks(
        self, 
        document_id: UUID, 
        chunks_data: List[dict]
    ) -> List[RagDocumentChunk]:
        """
        Bulk insert chunks for a document.
        
        Args:
            document_id: UUID of the parent document
            chunks_data: List of dicts with keys: idx, content, content_hash
            
        Returns:
            List of created RagDocumentChunk objects
        """
        chunks = []
        for chunk_data in chunks_data:
            chunk = RagDocumentChunk(
                document_id=document_id,
                idx=chunk_data["idx"],
                content=chunk_data["content"],
                content_hash=chunk_data["content_hash"],
            )
            chunks.append(chunk)
            self.session.add(chunk)
        
        await self.session.commit()
        
        # Refresh all chunks to get their IDs
        for chunk in chunks:
            await self.session.refresh(chunk)
        
        return chunks

    async def get_chunks_by_document_id(self, document_id: UUID) -> List[RagDocumentChunk]:
        """Get all chunks for a document, ordered by index."""
        result = await self.session.execute(
            select(RagDocumentChunk)
            .where(RagDocumentChunk.document_id == document_id)
            .order_by(RagDocumentChunk.idx)
        )
        return result.scalars().all()

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and all its chunks."""
        document = await self.get_by_id(document_id)
        if not document:
            return False
        
        await self.session.delete(document)
        await self.session.commit()
        return True
