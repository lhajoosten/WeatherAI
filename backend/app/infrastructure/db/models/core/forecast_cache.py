"""Forecast cache model (core schema)."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import CoreBase


class ForecastCache(CoreBase):
    __tablename__ = "forecast_cache"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    source = Column(String(100), nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    payload_json = Column(Text, nullable=False)

    location = relationship("Location", back_populates="forecast_cache")

__all__ = ["ForecastCache"]
