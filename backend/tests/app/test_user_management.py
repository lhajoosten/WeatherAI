"""Tests for user management functionality."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import User
from app.infrastructure.db import UserPreferencesRepository, UserProfileRepository


class TestUserProfileRepository:
    """Test UserProfileRepository."""

    @pytest.fixture
    async def user_profile_repo(self, db_session: AsyncSession):
        """Get user profile repository."""
        return UserProfileRepository(db_session)

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create a test user."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            timezone="UTC"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def test_create_profile(self, user_profile_repo: UserProfileRepository, test_user: User):
        """Test creating a user profile."""
        profile_data = {
            "display_name": "Test User",
            "bio": "This is a test user",
            "theme_preference": "dark"
        }

        profile = await user_profile_repo.create_or_update(test_user.id, **profile_data)

        assert profile.user_id == test_user.id
        assert profile.display_name == "Test User"
        assert profile.bio == "This is a test user"
        assert profile.theme_preference == "dark"
        assert profile.created_at is not None
        assert profile.updated_at is not None

    async def test_update_profile(self, user_profile_repo: UserProfileRepository, test_user: User):
        """Test updating a user profile."""
        # Create initial profile
        await user_profile_repo.create_or_update(test_user.id, display_name="Initial Name")

        # Update profile
        updated_profile = await user_profile_repo.create_or_update(
            test_user.id,
            display_name="Updated Name",
            bio="Updated bio"
        )

        assert updated_profile.display_name == "Updated Name"
        assert updated_profile.bio == "Updated bio"

    async def test_get_profile_by_user_id(self, user_profile_repo: UserProfileRepository, test_user: User):
        """Test getting profile by user ID."""
        # Create profile
        await user_profile_repo.create_or_update(test_user.id, display_name="Test User")

        # Get profile
        profile = await user_profile_repo.get_by_user_id(test_user.id)

        assert profile is not None
        assert profile.user_id == test_user.id
        assert profile.display_name == "Test User"


class TestUserPreferencesRepository:
    """Test UserPreferencesRepository."""

    @pytest.fixture
    async def user_preferences_repo(self, db_session: AsyncSession):
        """Get user preferences repository."""
        return UserPreferencesRepository(db_session)

    @pytest.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create a test user."""
        user = User(
            email="test2@example.com",
            password_hash="hashed_password",
            timezone="UTC"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def test_create_preferences(self, user_preferences_repo: UserPreferencesRepository, test_user: User):
        """Test creating user preferences."""
        preferences_data = {
            "units_system": "imperial",
            "show_wind": False,
            "show_humidity": True
        }

        preferences = await user_preferences_repo.create_or_update(test_user.id, **preferences_data)

        assert preferences.user_id == test_user.id
        assert preferences.units_system == "imperial"
        assert preferences.show_wind is False
        assert preferences.show_humidity is True
        assert preferences.show_precip is True  # Default value
        assert preferences.created_at is not None
        assert preferences.updated_at is not None

    async def test_update_preferences(self, user_preferences_repo: UserPreferencesRepository, test_user: User):
        """Test updating user preferences."""
        # Create initial preferences
        await user_preferences_repo.create_or_update(test_user.id, units_system="metric")

        # Update preferences
        updated_preferences = await user_preferences_repo.create_or_update(
            test_user.id,
            units_system="imperial",
            show_wind=False
        )

        assert updated_preferences.units_system == "imperial"
        assert updated_preferences.show_wind is False

    async def test_get_preferences_by_user_id(self, user_preferences_repo: UserPreferencesRepository, test_user: User):
        """Test getting preferences by user ID."""
        # Create preferences
        await user_preferences_repo.create_or_update(test_user.id, units_system="imperial")

        # Get preferences
        preferences = await user_preferences_repo.get_by_user_id(test_user.id)

        assert preferences is not None
        assert preferences.user_id == test_user.id
        assert preferences.units_system == "imperial"


# Note: These tests would need additional setup for async test database
# This is a basic structure following the existing test patterns in the project
