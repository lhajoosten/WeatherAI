"""Analytics & domain measurement models (core schema)."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship

from .base import CoreBase


class ObservationHourly(CoreBase):
    __tablename__ = "observation_hourly"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    observed_at = Column(DateTime, nullable=False)
    temp_c = Column(Float, nullable=True)
    wind_kph = Column(Float, nullable=True)
    precip_mm = Column(Float, nullable=True)
    humidity_pct = Column(Float, nullable=True)
    condition_code = Column(String(100), nullable=True)
    source = Column(String(100), nullable=False)
    raw_json = Column(Text, nullable=True)
    location = relationship("Location")
    __table_args__ = (Index("ix_observation_hourly_location_time", "location_id", "observed_at"),)


class ForecastHourly(CoreBase):
    __tablename__ = "forecast_hourly"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    forecast_issue_time = Column(DateTime, nullable=False)
    target_time = Column(DateTime, nullable=False)
    temp_c = Column(Float, nullable=True)
    precipitation_probability_pct = Column(Float, nullable=True)
    wind_kph = Column(Float, nullable=True)
    model_name = Column(String(100), nullable=True)
    source_run_id = Column(String(100), nullable=True)
    raw_json = Column(Text, nullable=True)
    location = relationship("Location")
    __table_args__ = (Index("ix_forecast_hourly_location_target", "location_id", "target_time"),)


class AggregationDaily(CoreBase):
    __tablename__ = "aggregation_daily"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    temp_min_c = Column(Float, nullable=True)
    temp_max_c = Column(Float, nullable=True)
    avg_temp_c = Column(Float, nullable=True)
    total_precip_mm = Column(Float, nullable=True)
    max_wind_kph = Column(Float, nullable=True)
    heating_degree_days = Column(Float, nullable=True)
    cooling_degree_days = Column(Float, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    location = relationship("Location")
    __table_args__ = (Index("ix_aggregation_daily_location_date", "location_id", "date"),)


class ForecastAccuracy(CoreBase):
    __tablename__ = "forecast_accuracy"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    target_time = Column(DateTime, nullable=False)
    forecast_issue_time = Column(DateTime, nullable=False)
    variable = Column(String(50), nullable=False)
    forecast_value = Column(Float, nullable=True)
    observed_value = Column(Float, nullable=True)
    abs_error = Column(Float, nullable=True)
    pct_error = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    location = relationship("Location")
    __table_args__ = (Index("ix_forecast_accuracy_location_target", "location_id", "target_time"),)


class TrendCache(CoreBase):
    __tablename__ = "trend_cache"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    metric = Column(String(100), nullable=False)
    period = Column(String(20), nullable=False)
    current_value = Column(Float, nullable=True)
    previous_value = Column(Float, nullable=True)
    delta = Column(Float, nullable=True)
    pct_change = Column(Float, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    location = relationship("Location")
    __table_args__ = (Index("ix_trend_cache_unique", "location_id", "metric", "period", unique=True),)


class AnalyticsQueryAudit(CoreBase):
    __tablename__ = "analytics_query_audit"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    endpoint = Column(String(100), nullable=False)
    params_json = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    rows_returned = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")


class ProviderRun(CoreBase):
    __tablename__ = "provider_run"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(100), nullable=False)
    run_type = Column(String(50), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)
    records_ingested = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    location = relationship("Location")
    __table_args__ = (Index("ix_provider_run_provider_type_started", "provider", "run_type", "started_at"),)


class AirQualityHourly(CoreBase):
    __tablename__ = "air_quality_hourly"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    observed_at = Column(DateTime, nullable=False)
    pm10 = Column(Float, nullable=True)
    pm2_5 = Column(Float, nullable=True)
    ozone = Column(Float, nullable=True)
    no2 = Column(Float, nullable=True)
    so2 = Column(Float, nullable=True)
    pollen_tree = Column(Float, nullable=True)
    pollen_grass = Column(Float, nullable=True)
    pollen_weed = Column(Float, nullable=True)
    source = Column(String(100), nullable=False)
    raw_json = Column(Text, nullable=True)
    location = relationship("Location")
    __table_args__ = (
        Index("ix_air_quality_hourly_location_time", "location_id", "observed_at"),
        Index("ix_air_quality_hourly_location_time_source", "location_id", "observed_at", "source", unique=True),
    )


class AstronomyDaily(CoreBase):
    __tablename__ = "astronomy_daily"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    sunrise_utc = Column(DateTime, nullable=True)
    sunset_utc = Column(DateTime, nullable=True)
    daylight_minutes = Column(Integer, nullable=True)
    moon_phase = Column(Float, nullable=True)
    civil_twilight_start_utc = Column(DateTime, nullable=True)
    civil_twilight_end_utc = Column(DateTime, nullable=True)
    generated_at = Column(DateTime, nullable=False)
    location = relationship("Location")
    __table_args__ = (Index("ix_astronomy_daily_location_date", "location_id", "date", unique=True),)


class DigestAudit(CoreBase):
    __tablename__ = "digest_audit"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    generated_at = Column(DateTime, nullable=False)
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


__all__ = [
    "ObservationHourly",
    "ForecastHourly",
    "AggregationDaily",
    "ForecastAccuracy",
    "TrendCache",
    "AnalyticsQueryAudit",
    "ProviderRun",
    "AirQualityHourly",
    "AstronomyDaily",
    "DigestAudit",
]
