"""Domain value objects for WeatherAI application.

Value objects are immutable objects that represent domain concepts
without identity. They help reduce primitive obsession.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocationId:
    """Value object for location identifiers."""
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("LocationId must be positive")


@dataclass(frozen=True)
class UserId:
    """Value object for user identifiers."""
    value: int

    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("UserId must be positive")


@dataclass(frozen=True)
class Coordinates:
    """Value object for geographic coordinates."""
    latitude: float
    longitude: float

    def __post_init__(self):
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError("Longitude must be between -180 and 180")


@dataclass(frozen=True)
class Temperature:
    """Value object for temperature with unit awareness."""
    value: float
    unit: str = "celsius"

    def __post_init__(self):
        if self.unit not in ("celsius", "fahrenheit", "kelvin"):
            raise ValueError("Temperature unit must be celsius, fahrenheit, or kelvin")

        # Basic sanity checks
        if self.unit == "kelvin" and self.value < 0:
            raise ValueError("Kelvin temperature cannot be negative")
        if self.unit == "celsius" and self.value < -273.15:
            raise ValueError("Celsius temperature cannot be below absolute zero")
        if self.unit == "fahrenheit" and self.value < -459.67:
            raise ValueError("Fahrenheit temperature cannot be below absolute zero")

    def to_celsius(self) -> Temperature:
        """Convert temperature to Celsius."""
        if self.unit == "celsius":
            return self
        elif self.unit == "fahrenheit":
            celsius_value = (self.value - 32) * 5/9
            return Temperature(celsius_value, "celsius")
        elif self.unit == "kelvin":
            celsius_value = self.value - 273.15
            return Temperature(celsius_value, "celsius")


@dataclass(frozen=True)
class DigestType:
    """Value object for digest types."""
    value: str

    def __post_init__(self):
        allowed_types = {"daily", "hourly", "weekly", "custom"}
        if self.value not in allowed_types:
            raise ValueError(f"DigestType must be one of {allowed_types}")


@dataclass(frozen=True)
class WeatherProvider:
    """Value object for weather data providers."""
    name: str
    api_version: str | None = None

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Provider name cannot be empty")
