"""Location & grouping models (core schema)."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float, ForeignKey, Index
from sqlalchemy.orm import relationship

from .base import CoreBase


class Location(CoreBase):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    timezone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="locations")
    forecast_cache = relationship("ForecastCache", back_populates="location", cascade="all, delete-orphan")
    group_memberships = relationship("LocationGroupMember", back_populates="location", cascade="all, delete-orphan")


class LocationGroup(CoreBase):
    __tablename__ = "location_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="location_groups")
    members = relationship("LocationGroupMember", back_populates="group", cascade="all, delete-orphan", lazy="raise")

    __table_args__ = (Index("ix_location_groups_user_name", "user_id", "name"),)


class LocationGroupMember(CoreBase):
    __tablename__ = "location_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("location_groups.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("LocationGroup", back_populates="members")
    location = relationship("Location", back_populates="group_memberships")

    __table_args__ = (Index("ix_location_group_members_unique", "group_id", "location_id", unique=True),)


__all__ = [
    "Location",
    "LocationGroup",
    "LocationGroupMember",
]
