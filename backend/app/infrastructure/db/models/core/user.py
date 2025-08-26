"""User and profile related models (core schema)."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from .base import CoreBase


class User(CoreBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    timezone = Column(String(50), default="UTC")
    prefs_json = Column(Text, nullable=True)  # Legacy JSON prefs
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    locations = relationship("Location", back_populates="user", cascade="all, delete-orphan")
    location_groups = relationship("LocationGroup", back_populates="user", cascade="all, delete-orphan")
    llm_audit = relationship("LLMAudit", back_populates="user")
    profile = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan", uselist=False)
    preferences = relationship("UserPreferences", back_populates="user", cascade="all, delete-orphan", uselist=False)


class UserProfile(CoreBase):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    display_name = Column(String(255), nullable=True)
    bio = Column(String(500), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    time_zone = Column(String(50), nullable=True)
    locale = Column(String(10), nullable=True)
    theme_preference = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")

    __table_args__ = (Index("ix_user_profiles_user_id", "user_id"),)


class UserPreferences(CoreBase):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    units_system = Column(String(20), default="metric")
    dashboard_default_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    show_wind = Column(Boolean, default=True)
    show_precip = Column(Boolean, default=True)
    show_humidity = Column(Boolean, default=True)
    json_settings = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")
    default_location = relationship("Location", foreign_keys=[dashboard_default_location_id])

    __table_args__ = (Index("ix_user_preferences_user_id", "user_id"),)


__all__ = [
    "User",
    "UserProfile",
    "UserPreferences",
]
