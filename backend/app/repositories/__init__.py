"""Repositories package for data access layer.

This package provides domain-specific repositories that encapsulate 
database operations and support the Unit of Work pattern.
"""

from .base import BaseRepository, UnitOfWork, get_uow
from .rag import RagDocumentRepository

# For backward compatibility, provide access to existing repositories
# from the old location until they are migrated
from app.db.repositories import (
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