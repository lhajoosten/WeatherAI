"""Domain exceptions for WeatherAI application.

This module defines the domain exception hierarchy used throughout the application.
All domain exceptions inherit from DomainError.
"""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Base domain exception for WeatherAI application."""

    def __init__(
        self,
        message: str,
        details: str | None = None,
        extra_data: dict[str, Any] | None = None
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


# Phase 4 exceptions for frontend i18n mapping
class RateLimitExceededError(DomainError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, limit: int, window_seconds: int, endpoint: str):
        self.limit = limit
        self.window_seconds = window_seconds
        self.endpoint = endpoint
        message = f"Rate limit exceeded: {limit} requests per {window_seconds}s for {endpoint}"
        super().__init__(message, extra_data={
            "limit": limit,
            "window_seconds": window_seconds,
            "endpoint": endpoint,
            "error_code": "rate_limited"
        })


class QueryValidationError(ValidationError):
    """Raised when query validation fails."""
    
    def __init__(self, message: str, query_length: int | None = None, max_length: int | None = None):
        self.query_length = query_length
        self.max_length = max_length
        extra_data = {"error_code": "validation_error"}
        if query_length is not None:
            extra_data["query_length"] = query_length
        if max_length is not None:
            extra_data["max_length"] = max_length
        super().__init__(message, extra_data=extra_data)


class NoContextAvailableError(RAGError):
    """Raised when no relevant context is available (guardrail triggered)."""
    
    def __init__(self, threshold: float, max_similarity: float | None = None):
        self.threshold = threshold
        self.max_similarity = max_similarity
        message = f"No relevant context found above similarity threshold {threshold}"
        if max_similarity is not None:
            message += f" (max similarity: {max_similarity:.3f})"
        super().__init__(message, extra_data={
            "threshold": threshold,
            "max_similarity": max_similarity,
            "error_code": "no_context"
        })


class RetrievalTimeoutError(RAGError):
    """Raised when retrieval takes too long."""
    
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        message = f"Retrieval timed out after {timeout_seconds}s"
        super().__init__(message, extra_data={
            "timeout_seconds": timeout_seconds,
            "error_code": "retrieval_timeout"
        })


class InternalProcessingError(DomainError):
    """Raised for internal processing errors that should be mapped to internal_error."""
    
    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        extra_data = {"error_code": "internal_error"}
        if original_error:
            extra_data["original_error_type"] = type(original_error).__name__
            extra_data["original_error_message"] = str(original_error)
        super().__init__(message, extra_data=extra_data)
