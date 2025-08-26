"""User schema models for authentication and profile management."""

from .auth import UserCreateRequest, UserLoginRequest, TokenResponse
from .profile import (
    UserProfileUpdateRequest,
    UserPreferencesUpdateRequest,
    UserResponse,
    UserProfileResponse,
    UserPreferencesResponse,
    UserMeResponse,
    AvatarUploadResponse,
)

__all__ = [
    # Auth
    "UserCreateRequest",
    "UserLoginRequest", 
    "TokenResponse",
    # Profile
    "UserProfileUpdateRequest",
    "UserPreferencesUpdateRequest",
    "UserResponse",
    "UserProfileResponse",
    "UserPreferencesResponse",
    "UserMeResponse",
    "AvatarUploadResponse",
]