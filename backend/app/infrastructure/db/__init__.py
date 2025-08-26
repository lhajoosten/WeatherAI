"""Database infrastructure public API.

Exports:
- Unit of Work & base repository patterns
- Domain repositories (user, location, analytics, RAG, etc.)
- Model bases for Alembic (CoreBase, RagBase) and backward compatible `Base`
"""

from .base import BaseRepository, UnitOfWork, get_uow

# Repositories (split into dedicated modules under repositories/)
from .repositories import (
    UserRepository,
    UserProfileRepository,
    UserPreferencesRepository,
    LocationRepository,
    ForecastCacheRepository,
    LLMAuditRepository,
    RagDocumentRepository,
    # Analytics / domain specific
    ObservationRepository,
    ForecastRepository,  # ForecastHourly analytics repository
    AggregationRepository,
    AccuracyRepository,
    TrendRepository,
    AnalyticsAuditRepository,
    ProviderRunRepository,
    AirQualityRepository,
    AstronomyRepository,
)

# Model bases (importing from models package)
from .models import CoreBase, RagBase, Base

__all__ = [
    # Base patterns
    "BaseRepository",
    "UnitOfWork",
    "get_uow",
    # Repositories
    "UserRepository",
    "UserProfileRepository",
    "UserPreferencesRepository",
    "LocationRepository",
    "ForecastCacheRepository",
    "LLMAuditRepository",
    "RagDocumentRepository",
    "ObservationRepository",
    "ForecastRepository",
    "AggregationRepository",
    "AccuracyRepository",
    "TrendRepository",
    "AnalyticsAuditRepository",
    "ProviderRunRepository",
    "AirQualityRepository",
    "AstronomyRepository",
    # Model bases
    "CoreBase",
    "RagBase",
    "Base",
]