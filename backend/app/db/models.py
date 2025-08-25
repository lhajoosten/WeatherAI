from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model for authentication and profile data."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    timezone = Column(String(50), default="UTC")
    prefs_json = Column(Text, nullable=True)  # JSON string for user preferences (legacy)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    locations = relationship("Location", back_populates="user", cascade="all, delete-orphan")
    location_groups = relationship("LocationGroup", back_populates="user", cascade="all, delete-orphan")
    llm_audit = relationship("LLMAudit", back_populates="user")
    profile = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    preferences = relationship("UserPreferences", back_populates="user", cascade="all, delete-orphan", uselist=False)


class UserProfile(Base):
    """User profile data for personalization."""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    display_name = Column(String(255), nullable=True)
    bio = Column(String(500), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    time_zone = Column(String(50), nullable=True)
    locale = Column(String(10), nullable=True)  # e.g., "en-US", "es-ES"
    theme_preference = Column(String(20), nullable=True)  # "light", "dark", "system"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="profile")

    # Index for efficient queries
    __table_args__ = (
        Index('ix_user_profiles_user_id', 'user_id'),
    )


class UserPreferences(Base):
    """User preferences for weather display and functionality."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    # Weather display preferences
    units_system = Column(String(20), default="metric")  # "metric" or "imperial"
    dashboard_default_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    show_wind = Column(Boolean, default=True)
    show_precip = Column(Boolean, default=True)
    show_humidity = Column(Boolean, default=True)
    # JSON settings for extensibility (SQL Server compatible)
    json_settings = Column(Text, nullable=True)  # Additional preferences as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")
    default_location = relationship("Location", foreign_keys=[dashboard_default_location_id])

    # Index for efficient queries
    __table_args__ = (
        Index('ix_user_preferences_user_id', 'user_id'),
    )


class Location(Base):
    """User's saved locations for weather tracking."""
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)  # e.g., "Home", "Office", "Seattle, WA"
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    timezone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="locations")
    forecast_cache = relationship("ForecastCache", back_populates="location", cascade="all, delete-orphan")
    group_memberships = relationship("LocationGroupMember", back_populates="location", cascade="all, delete-orphan")


class LocationGroup(Base):
    """User-defined groups for organizing locations."""
    __tablename__ = "location_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="location_groups")
    members = relationship("LocationGroupMember", back_populates="group", cascade="all, delete-orphan", lazy="raise")

    # Index for efficient queries
    __table_args__ = (
        Index('ix_location_groups_user_name', 'user_id', 'name'),
    )


class LocationGroupMember(Base):
    """Membership relationship between locations and groups."""
    __tablename__ = "location_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("location_groups.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("LocationGroup", back_populates="members")
    location = relationship("Location", back_populates="group_memberships")

    # Unique constraint to prevent duplicate memberships
    __table_args__ = (
        Index('ix_location_group_members_unique', 'group_id', 'location_id', unique=True),
    )


class ForecastCache(Base):
    """Cached weather forecast data from external providers."""
    __tablename__ = "forecast_cache"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    source = Column(String(100), nullable=False)  # e.g., "open-meteo", "noaa"
    fetched_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    payload_json = Column(Text, nullable=False)  # Raw JSON response from weather API

    # Relationships
    location = relationship("Location", back_populates="forecast_cache")


class LLMAudit(Base):
    """Audit log for LLM API calls with token usage and cost tracking."""
    __tablename__ = "llm_audit"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system calls
    endpoint = Column(String(100), nullable=False)  # e.g., "explain", "chat"
    model = Column(String(100), nullable=False)  # e.g., "gpt-4", "gpt-3.5-turbo"
    prompt_summary = Column(String(200), nullable=False)  # Truncated prompt for debugging (no PII)
    tokens_in = Column(Integer, nullable=False)
    tokens_out = Column(Integer, nullable=False)
    cost = Column(Float, nullable=True)  # USD cost, nullable until cost calculation is implemented
    has_air_quality = Column(Boolean, nullable=True)  # Forward compatibility flag
    has_astronomy = Column(Boolean, nullable=True)  # Forward compatibility flag
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="llm_audit")


# Analytics Models for Phase 1

class ObservationHourly(Base):
    """Hourly weather observations from external sources."""
    __tablename__ = "observation_hourly"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    observed_at = Column(DateTime, nullable=False)  # UTC timestamp
    temp_c = Column(Float, nullable=True)
    wind_kph = Column(Float, nullable=True)
    precip_mm = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    condition_code = Column(String(100), nullable=True)
    source = Column(String(100), nullable=False)  # e.g., "open-meteo", "noaa"
    raw_json = Column(Text, nullable=True)  # Raw JSON for debugging

    # Relationships
    location = relationship("Location")

    # Index for efficient queries
    __table_args__ = (
        Index('ix_observation_hourly_location_time', 'location_id', 'observed_at'),
    )


class ForecastHourly(Base):
    """Hourly forecast data normalized from provider responses."""
    __tablename__ = "forecast_hourly"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    forecast_issue_time = Column(DateTime, nullable=False)  # When forecast was issued
    target_time = Column(DateTime, nullable=False)  # Time being forecasted
    temp_c = Column(Float, nullable=True)
    precipitation_probability_pct = Column(Float, nullable=True)
    wind_kph = Column(Float, nullable=True)
    model_name = Column(String(100), nullable=True)  # Weather model name
    source_run_id = Column(String(100), nullable=True)  # Provider's run identifier
    raw_json = Column(Text, nullable=True)  # Raw JSON for debugging

    # Relationships
    location = relationship("Location")

    # Index for efficient queries
    __table_args__ = (
        Index('ix_forecast_hourly_location_target', 'location_id', 'target_time'),
    )


class AggregationDaily(Base):
    """Daily aggregated weather data computed from hourly observations."""
    __tablename__ = "aggregation_daily"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    date = Column(DateTime, nullable=False)  # Date (midnight UTC)
    temp_min_c = Column(Float, nullable=True)
    temp_max_c = Column(Float, nullable=True)
    avg_temp_c = Column(Float, nullable=True)
    total_precip_mm = Column(Float, nullable=True)
    max_wind_kph = Column(Float, nullable=True)
    heating_degree_days = Column(Float, nullable=True)  # Base 18°C
    cooling_degree_days = Column(Float, nullable=True)  # Base 18°C
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    location = relationship("Location")

    # Index for efficient queries
    __table_args__ = (
        Index('ix_aggregation_daily_location_date', 'location_id', 'date'),
    )


class ForecastAccuracy(Base):
    """Forecast accuracy metrics comparing predictions vs observations."""
    __tablename__ = "forecast_accuracy"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    target_time = Column(DateTime, nullable=False)  # Time being evaluated
    forecast_issue_time = Column(DateTime, nullable=False)  # When forecast was made
    variable = Column(String(50), nullable=False)  # e.g., "temp_c", "precipitation_probability_pct"
    forecast_value = Column(Float, nullable=True)
    observed_value = Column(Float, nullable=True)
    abs_error = Column(Float, nullable=True)  # |forecast - observed|
    pct_error = Column(Float, nullable=True)  # abs_error / observed * 100
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    location = relationship("Location")

    # Index for efficient queries
    __table_args__ = (
        Index('ix_forecast_accuracy_location_target', 'location_id', 'target_time'),
    )


class TrendCache(Base):
    """Cached trend calculations for common metrics and periods."""
    __tablename__ = "trend_cache"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    metric = Column(String(100), nullable=False)  # e.g., "temp_c", "total_precip_mm"
    period = Column(String(20), nullable=False)  # e.g., "7d", "30d"
    current_value = Column(Float, nullable=True)
    previous_value = Column(Float, nullable=True)
    delta = Column(Float, nullable=True)  # current - previous
    pct_change = Column(Float, nullable=True)  # (delta / previous) * 100
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    location = relationship("Location")

    # Unique constraint to ensure one trend per location/metric/period
    __table_args__ = (
        Index('ix_trend_cache_unique', 'location_id', 'metric', 'period', unique=True),
    )


class AnalyticsQueryAudit(Base):
    """Audit log for analytics API calls."""
    __tablename__ = "analytics_query_audit"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    endpoint = Column(String(100), nullable=False)  # Analytics endpoint called
    params_json = Column(Text, nullable=True)  # JSON of query parameters
    duration_ms = Column(Integer, nullable=True)  # Query execution time
    rows_returned = Column(Integer, nullable=True)  # Number of rows returned
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")


class ProviderRun(Base):
    """Track provider ingestion runs with status and metadata."""
    __tablename__ = "provider_run"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(100), nullable=False)  # e.g., "openmeteo", "metar"
    run_type = Column(String(50), nullable=False)  # e.g., "forecast", "observation", "air_quality", "astronomy"
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Nullable for global runs
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # SUCCESS, FAILED, RUNNING
    records_ingested = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    location = relationship("Location")

    # Index for efficient queries
    __table_args__ = (
        Index('ix_provider_run_provider_type_started', 'provider', 'run_type', 'started_at'),
    )


class AirQualityHourly(Base):
    """Hourly air quality and pollen data."""
    __tablename__ = "air_quality_hourly"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    observed_at = Column(DateTime, nullable=False)
    pm10 = Column(Float, nullable=True)  # PM10 particulate matter
    pm2_5 = Column(Float, nullable=True)  # PM2.5 particulate matter
    ozone = Column(Float, nullable=True)  # O3 ozone
    no2 = Column(Float, nullable=True)  # NO2 nitrogen dioxide
    so2 = Column(Float, nullable=True)  # SO2 sulfur dioxide
    pollen_tree = Column(Float, nullable=True)  # Tree pollen count
    pollen_grass = Column(Float, nullable=True)  # Grass pollen count
    pollen_weed = Column(Float, nullable=True)  # Weed pollen count
    source = Column(String(100), nullable=False)  # Provider source
    raw_json = Column(Text, nullable=True)  # Raw JSON for debugging

    # Relationships
    location = relationship("Location")

    # Indexes for efficient queries and uniqueness
    __table_args__ = (
        Index('ix_air_quality_hourly_location_time', 'location_id', 'observed_at'),
        Index('ix_air_quality_hourly_location_time_source', 'location_id', 'observed_at', 'source', unique=True),
    )


class AstronomyDaily(Base):
    """Daily astronomical data computed locally."""
    __tablename__ = "astronomy_daily"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    date = Column(DateTime, nullable=False)  # Date (UTC)
    sunrise_utc = Column(DateTime, nullable=True)
    sunset_utc = Column(DateTime, nullable=True)
    daylight_minutes = Column(Integer, nullable=True)  # Minutes of daylight
    moon_phase = Column(Float, nullable=True)  # 0.0 = new moon, 1.0 = full moon
    civil_twilight_start_utc = Column(DateTime, nullable=True)
    civil_twilight_end_utc = Column(DateTime, nullable=True)
    generated_at = Column(DateTime, nullable=False)

    # Relationships
    location = relationship("Location")

    # Index for efficient queries
    __table_args__ = (
        Index('ix_astronomy_daily_location_date', 'location_id', 'date', unique=True),
    )

class DigestAudit(Base):
    __tablename__ = "digest_audit"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    cache_hit = Column(Boolean, nullable=False)
    forecast_signature = Column(String(64), index=True)
    preferences_hash = Column(String(64))
    prompt_version = Column(String(50), index=True)
    model_name = Column(String(100))
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    latency_ms_preprocess = Column(Integer)
    latency_ms_llm = Column(Integer)
    latency_ms_total = Column(Integer)
    reason = Column(String(30))
    comfort_score = Column(Float)
    temp_peak_c = Column(Float)
    temp_peak_hour = Column(Integer)
    wind_peak_kph = Column(Float)
    wind_peak_hour = Column(Integer)
    rain_windows_json = Column(Text)
    activity_block_json = Column(Text)

    user = relationship("User")