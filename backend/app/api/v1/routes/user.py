"""User management API endpoints."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import (
    check_rate_limit,
    get_current_user,
    get_user_preferences_repository,
    get_user_profile_repository,
)
from app.infrastructure.db.models import User
from app.infrastructure.db import UserPreferencesRepository, UserProfileRepository
from app.application.dto.dto import (
    AvatarUploadResponse,
    UserMeResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserProfileResponse,
    UserProfileUpdate,
)

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_extended(
    current_user: User = Depends(get_current_user),
    profile_repo: UserProfileRepository = Depends(get_user_profile_repository),
    preferences_repo: UserPreferencesRepository = Depends(get_user_preferences_repository)
):
    """Get current user with profile and preferences."""
    await check_rate_limit("user_me", current_user)

    # Get profile and preferences
    profile = await profile_repo.get_by_user_id(current_user.id)
    preferences = await preferences_repo.get_by_user_id(current_user.id)

    # Build response
    response_data = {
        "id": current_user.id,
        "email": current_user.email,
        "timezone": current_user.timezone,
        "created_at": current_user.created_at,
        "profile": UserProfileResponse.model_validate(profile) if profile else None,
        "preferences": UserPreferencesResponse.model_validate(preferences) if preferences else None,
    }

    return UserMeResponse.model_validate(response_data)


@router.patch("/profile", response_model=UserProfileResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    profile_repo: UserProfileRepository = Depends(get_user_profile_repository)
):
    """Update user profile."""
    await check_rate_limit("user_profile_update", current_user)

    # Filter out None values
    update_data = {k: v for k, v in profile_data.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid update fields provided"
        )

    # Create or update profile
    profile = await profile_repo.create_or_update(current_user.id, **update_data)

    return UserProfileResponse.model_validate(profile)


@router.patch("/preferences", response_model=UserPreferencesResponse)
async def update_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    preferences_repo: UserPreferencesRepository = Depends(get_user_preferences_repository)
):
    """Update user preferences."""
    await check_rate_limit("user_preferences_update", current_user)

    # Filter out None values
    update_data = {k: v for k, v in preferences_data.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid update fields provided"
        )

    # Create or update preferences
    preferences = await preferences_repo.create_or_update(current_user.id, **update_data)

    return UserPreferencesResponse.model_validate(preferences)


@router.post("/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    profile_repo: UserProfileRepository = Depends(get_user_profile_repository)
):
    """Upload user avatar (stub implementation)."""
    await check_rate_limit("user_avatar_upload", current_user)

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    # Validate file size (5MB limit)
    if file.size and file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )

    # For now, generate a stub URL (in production, this would upload to storage)
    # This is a placeholder implementation as requested in the problem statement
    stub_url = f"/assets/avatars/user_{current_user.id}_{file.filename}"

    # Update profile with avatar URL
    await profile_repo.create_or_update(current_user.id, avatar_url=stub_url)

    return AvatarUploadResponse(avatar_url=stub_url)
