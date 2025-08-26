"""User authentication schemas."""

from pydantic import BaseModel, EmailStr, Field
from .profile import UserResponse


class UserCreateRequest(BaseModel):
    """Request schema for user creation."""
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)


class UserLoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse