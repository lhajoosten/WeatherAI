"""Repositories package for data access layer.

This package provides domain-specific repositories that encapsulate 
database operations and support the Unit of Work pattern.
"""

from .base import BaseRepository, UnitOfWork, get_uow
from .rag import RagDocumentRepository

# Import existing repositories from this module
from .repositories import (
    UserRepository,
    UserProfileRepository, 
    UserPreferencesRepository,
    LocationRepository,
    ForecastRepository,
    LLMAuditRepository,
)

__all__ = [
    # Base patterns
    "BaseRepository",
    "UnitOfWork", 
    "get_uow",
    # Domain repositories
    "RagDocumentRepository",
    # Legacy repositories (backward compatibility)
    "UserRepository",
    "UserProfileRepository",
    "UserPreferencesRepository", 
    "LocationRepository",
    "ForecastRepository",
    "LLMAuditRepository",
]