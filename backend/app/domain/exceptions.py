"""Domain exceptions for WeatherAI application.

This module defines the domain exception hierarchy used throughout the application.
All domain exceptions inherit from DomainError.
"""

from __future__ import annotations
from typing import Any, Dict, Optional


class DomainError(Exception):
    """Base domain exception for WeatherAI application."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details
        self.extra_data = extra_data or {}


class ValidationError(DomainError):
    """Raised when domain validation rules are violated."""
    pass


class NotFoundError(DomainError):
    """Raised when a requested domain entity is not found."""
    pass


class ConflictError(DomainError):
    """Raised when a domain constraint conflict occurs."""
    pass


class BusinessRuleViolationError(DomainError):
    """Raised when a business rule is violated."""
    pass


class ForecastUnavailableError(DomainError):
    """Raised when forecast data is unavailable or cannot be retrieved."""
    pass


class InvalidDateFormatError(ValidationError):
    """Raised when an invalid date format is provided."""
    pass


class UserPreferencesError(DomainError):
    """Raised when user preferences cannot be retrieved or are invalid."""
    pass


class DigestGenerationError(DomainError):
    """Raised when digest generation fails."""
    pass


# RAG-specific domain exceptions
class RAGError(DomainError):
    """Base exception for RAG pipeline domain errors."""
    pass


class LowSimilarityError(RAGError):
    """Raised when retrieved documents have similarity below threshold."""
    
    def __init__(self, threshold: float, max_similarity: float | None = None):
        self.threshold = threshold
        self.max_similarity = max_similarity
        message = f"All retrieved documents below similarity threshold {threshold}"
        if max_similarity is not None:
            message += f" (max similarity: {max_similarity:.3f})"
        super().__init__(message)


class EmptyContextError(RAGError):
    """Raised when no context is available for generation."""
    pass