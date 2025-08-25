"""Domain exceptions for WeatherAI application.

This module defines custom exceptions used throughout the application
to provide clear error handling and proper HTTP status code mapping.
"""

from typing import Any, Dict, Optional


class WeatherAIException(Exception):
    """Base exception for WeatherAI application."""

    def __init__(self, message: str, status_code: int = 500):
        """Initialize exception with message and HTTP status code.

        Args:
            message: Error message
            status_code: HTTP status code to return
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# New hierarchical exception structure
class AppError(Exception):
    """Base application exception for the new exception hierarchy."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        details: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details
        self.extra_data = extra_data or {}


class ValidationError(AppError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, status_code=422, details=details)


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str, identifier: Any):
        message = f"{resource} not found"
        details = f"No {resource.lower()} found with identifier: {identifier}"
        super().__init__(message, status_code=404, details=details)


class ConflictError(AppError):
    """Raised when a resource conflict occurs."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, status_code=409, details=details)


class RateLimitError(AppError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[str] = None):
        super().__init__(message, status_code=429, details=details)


class ServiceUnavailableError(AppError):
    """Raised when a required service is unavailable."""
    
    def __init__(self, service: str, details: Optional[str] = None):
        message = f"{service} service unavailable"
        super().__init__(message, status_code=503, details=details)


class ForecastUnavailableError(WeatherAIException):
    """Raised when forecast data is unavailable or cannot be retrieved."""

    def __init__(self, message: str = "Forecast data is currently unavailable"):
        super().__init__(message, status_code=503)


class InvalidDateFormatError(WeatherAIException):
    """Raised when an invalid date format is provided."""

    def __init__(self, message: str = "Invalid date format. Expected YYYY-MM-DD"):
        super().__init__(message, status_code=400)


class UserPreferencesError(WeatherAIException):
    """Raised when user preferences cannot be retrieved or are invalid."""

    def __init__(self, message: str = "Unable to retrieve user preferences"):
        super().__init__(message, status_code=500)


class DigestGenerationError(WeatherAIException):
    """Raised when digest generation fails."""

    def __init__(self, message: str = "Failed to generate digest"):
        super().__init__(message, status_code=500)


class CacheError(WeatherAIException):
    """Raised when cache operations fail."""

    def __init__(self, message: str = "Cache operation failed"):
        super().__init__(message, status_code=500)
