"""Provider abstractions for weather data ingestion."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class ForecastProvider(ABC):
    """Abstract base class for forecast data providers."""

    @abstractmethod
    async def fetch_forecast(self, location_id: int, lat: float, lon: float) -> list[dict[str, Any]]:
        """Fetch forecast data for a location.
        
        Args:
            location_id: Database location ID
            lat: Latitude
            lon: Longitude
            
        Returns:
            List of forecast records in normalized format
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'openmeteo')."""
        pass


class ObservationProvider(ABC):
    """Abstract base class for observation data providers."""

    @abstractmethod
    async def fetch_observations(self, location_id: int, lat: float, lon: float, hours_back: int = 24) -> list[dict[str, Any]]:
        """Fetch observation data for a location.
        
        Args:
            location_id: Database location ID
            lat: Latitude
            lon: Longitude
            hours_back: Number of hours of historical data to fetch
            
        Returns:
            List of observation records in normalized format
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'openmeteo', 'metar')."""
        pass


class AirQualityProvider(ABC):
    """Abstract base class for air quality data providers."""

    @abstractmethod
    async def fetch_air_quality(self, location_id: int, lat: float, lon: float, hours_back: int = 24) -> list[dict[str, Any]]:
        """Fetch air quality data for a location.
        
        Args:
            location_id: Database location ID
            lat: Latitude
            lon: Longitude
            hours_back: Number of hours of historical data to fetch
            
        Returns:
            List of air quality records in normalized format
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'openmeteo')."""
        pass