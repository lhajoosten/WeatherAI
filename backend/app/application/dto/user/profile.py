"""User profile and preferences schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """User response DTO."""
    id: int
    email: str
    timezone: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """User profile response DTO."""
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    time_zone: str | None = None
    locale: str | None = None
    theme_preference: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class UserPreferencesResponse(BaseModel):
    """User preferences response DTO."""
    units_system: str = "metric"
    dashboard_default_location_id: int | None = None
    show_wind: bool = True
    show_precip: bool = True
    show_humidity: bool = True
    json_settings: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    """Request schema for user profile updates."""
    display_name: str | None = Field(default=None, max_length=255)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=500)
    time_zone: str | None = Field(default=None, max_length=50)
    locale: str | None = Field(default=None, max_length=10)
    theme_preference: str | None = Field(default=None, max_length=20)


class UserPreferencesUpdateRequest(BaseModel):
    """Request schema for user preferences updates."""
    units_system: str | None = Field(default=None, pattern="^(metric|imperial)$")
    dashboard_default_location_id: int | None = None
    show_wind: bool | None = None
    show_precip: bool | None = None
    show_humidity: bool | None = None
    json_settings: str | None = None


class UserMeResponse(BaseModel):
    """Extended user response with profile and preferences."""
    id: int
    email: str
    timezone: str
    created_at: datetime
    profile: UserProfileResponse | None = None
    preferences: UserPreferencesResponse | None = None

    class Config:
        from_attributes = True


class AvatarUploadResponse(BaseModel):
    """Response schema for avatar upload."""
    avatar_url: str
    message: str = "Avatar uploaded successfully"