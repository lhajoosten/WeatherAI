"""Domain exceptions for WeatherAI application.

This module defines custom exceptions used throughout the application
to provide clear error handling and proper HTTP status code mapping.
"""


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