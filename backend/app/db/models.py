from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Boolean
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
    prefs_json = Column(Text, nullable=True)  # JSON string for user preferences
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    locations = relationship("Location", back_populates="user", cascade="all, delete-orphan")
    llm_audit = relationship("LLMAudit", back_populates="user")


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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="llm_audit")