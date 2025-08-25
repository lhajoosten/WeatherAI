"""Weather data client interfaces and implementations.

This module provides abstractions for external weather data providers
with consistent interfaces and error handling.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.domain.value_objects import Coordinates, WeatherProvider
from app.domain.exceptions import DomainError


class WeatherDataError(DomainError):
    """Raised when weather data cannot be retrieved."""
    pass


class WeatherClient(ABC):
    """Abstract base class for weather data clients."""
    
    @property
    @abstractmethod
    def provider(self) -> WeatherProvider:
        """The weather provider information."""
        pass
    
    @abstractmethod
    async def get_current_weather(
        self, 
        coordinates: Coordinates
    ) -> Dict[str, Any]:
        """Get current weather for given coordinates."""
        pass
    
    @abstractmethod
    async def get_forecast(
        self, 
        coordinates: Coordinates,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get weather forecast for given coordinates."""
        pass


class OpenMeteoClient(WeatherClient):
    """OpenMeteo weather data client implementation."""
    
    def __init__(self, base_url: str = "https://api.open-meteo.com/v1"):
        self.base_url = base_url
    
    @property
    def provider(self) -> WeatherProvider:
        return WeatherProvider(name="open-meteo", api_version="v1")
    
    async def get_current_weather(
        self, 
        coordinates: Coordinates
    ) -> Dict[str, Any]:
        """Get current weather from OpenMeteo API."""
        # Placeholder implementation - would use httpx in real implementation
        return {
            "temperature": 20.0,
            "humidity": 65,
            "wind_speed": 10.5,
            "description": "partly cloudy",
            "provider": self.provider.name,
            "coordinates": {
                "latitude": coordinates.latitude,
                "longitude": coordinates.longitude
            }
        }
    
    async def get_forecast(
        self, 
        coordinates: Coordinates,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get weather forecast from OpenMeteo API."""
        # Placeholder implementation - would use httpx in real implementation
        forecast = []
        for i in range(hours):
            forecast.append({
                "hour": i,
                "temperature": 20.0 + (i % 12) - 6,
                "humidity": 65 + (i % 10),
                "wind_speed": 10.5 + (i % 5),
                "description": "variable"
            })
        return forecast


class MockWeatherClient(WeatherClient):
    """Mock weather client for testing."""
    
    @property
    def provider(self) -> WeatherProvider:
        return WeatherProvider(name="mock", api_version="test")
    
    async def get_current_weather(
        self, 
        coordinates: Coordinates
    ) -> Dict[str, Any]:
        """Get mock current weather."""
        return {
            "temperature": 22.0,
            "humidity": 70,
            "wind_speed": 8.0,
            "description": "mock sunny",
            "provider": self.provider.name
        }
    
    async def get_forecast(
        self, 
        coordinates: Coordinates,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get mock weather forecast."""
        return [
            {
                "hour": i,
                "temperature": 22.0,
                "humidity": 70,
                "wind_speed": 8.0,
                "description": "mock conditions"
            }
            for i in range(hours)
        ]