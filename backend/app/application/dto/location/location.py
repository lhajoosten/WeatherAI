"""Location schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class LocationCreateRequest(BaseModel):
    """Request schema for location creation."""
    name: str = Field(max_length=255)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    timezone: str | None = Field(default=None, max_length=50)


class LocationUpdateRequest(BaseModel):
    """Request schema for location updates."""
    name: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, max_length=50)


class LocationResponse(BaseModel):
    """Location response DTO."""
    id: int
    name: str
    lat: float
    lon: float
    timezone: str | None
    created_at: datetime

    class Config:
        from_attributes = True