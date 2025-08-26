"""Pydantic schemas for Morning Digest feature."""

from datetime import datetime

from pydantic import BaseModel, Field

# Schema version constant
SCHEMA_VERSION = "1.0"


class Window(BaseModel):
    """Time window for specific metrics (e.g., peak rain window)."""
    start_hour: int = Field(..., description="Start hour (0-23)")
    end_hour: int = Field(..., description="End hour (0-23)")
    duration_hours: int = Field(..., description="Duration in hours")


class ActivityBlock(BaseModel):
    """Activity recommendation block based on weather conditions."""
    activity_type: str = Field(..., description="Type of activity (indoor/outdoor/mixed)")
    time_window: Window = Field(..., description="Recommended time window")
    conditions: str = Field(..., description="Weather conditions description")
    suitability_score: float = Field(..., ge=0.0, le=1.0, description="Suitability score (0-1)")


class Derived(BaseModel):
    """Derived metrics from weather data."""
    temp_min_c: float = Field(..., description="Minimum temperature in Celsius")
    temp_max_c: float = Field(..., description="Maximum temperature in Celsius")
    peak_rain_window: Window | None = Field(None, description="1-hour window with maximum rainfall")
    lowest_wind_window: Window | None = Field(None, description="Window with lowest wind speeds")
    comfort_score: float = Field(..., ge=0.0, le=1.0, description="Overall comfort score (0-1)")
    activity_blocks: list[ActivityBlock] = Field(default_factory=list, description="Activity recommendations")


class Bullet(BaseModel):
    """Individual bullet point in the summary."""
    text: str = Field(..., description="Bullet point text")
    category: str = Field(..., description="Category (weather/activity/alert)")
    priority: int = Field(..., ge=1, le=3, description="Priority level (1=high, 3=low)")


class Summary(BaseModel):
    """Summary narrative and bullet points."""
    narrative: str = Field(..., description="Main summary narrative")
    bullets: list[Bullet] = Field(..., description="Action items and key points")
    driver: str = Field(..., description="Main weather driver for the day")


class TokensMeta(BaseModel):
    """Token usage metadata (null in PR1, for future LLM integration)."""
    tokens_in: int | None = Field(None, description="Input tokens used")
    tokens_out: int | None = Field(None, description="Output tokens generated")
    model: str | None = Field(None, description="Model used for generation")
    cost_usd: float | None = Field(None, description="Estimated cost in USD")


class CacheMeta(BaseModel):
    """Cache metadata for the digest response."""
    hit: bool = Field(..., description="Whether this was a cache hit")
    ttl_seconds: int | None = Field(None, description="TTL remaining (if hit) or full TTL (if miss)")
    key: str = Field(..., description="Cache key used")
    generated_at: datetime = Field(..., description="When the digest was generated")


class DigestResponse(BaseModel):
    """Complete morning digest response."""
    schema_version: str = Field(default=SCHEMA_VERSION, description="Schema version")
    date: str = Field(..., description="Date for the digest (YYYY-MM-DD)")
    location_id: int = Field(..., description="Location ID for the digest")
    user_id: str = Field(..., description="User ID who requested the digest")
    summary: Summary = Field(..., description="Summary narrative and bullets")
    derived: Derived = Field(..., description="Derived weather metrics")
    tokens_meta: TokensMeta | None = Field(None, description="Token usage (null in PR1)")
    cache_meta: CacheMeta = Field(..., description="Cache metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
