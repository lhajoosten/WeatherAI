"""Unified models package with modular structure.

Legacy single-file `models.py` has been decomposed into multiple modules under
`models/core` and `models/rag`. We preserve backward compatibility by exporting
the previous symbols (e.g. `RagDocument`) mapped onto the new schema-specific
models (`Document`).
"""

from .core import CoreBase  # Base for core/public tables
from .rag import RagBase, Document, DocumentChunk  # RAG schema models

# Core domain models
from .core.user import User, UserProfile, UserPreferences
from .core.location import Location, LocationGroup, LocationGroupMember
from .core.forecast_cache import ForecastCache
from .core.llm_audit import LLMAudit
from .core.analytics import (
    ObservationHourly,
    ForecastHourly,
    AggregationDaily,
    ForecastAccuracy,
    TrendCache,
    AnalyticsQueryAudit,
    ProviderRun,
    AirQualityHourly,
    AstronomyDaily,
    DigestAudit,
)

# Backward compatibility aliases (legacy naming)
RagDocument = Document
RagDocumentChunk = DocumentChunk

# Provide a generic Base alias expected by Alembic or legacy code
Base = CoreBase

__all__ = [
    # Bases
    "Base",
    "CoreBase",
    "RagBase",
    # Core models
    "User",
    "UserProfile",
    "UserPreferences",
    "Location",
    "LocationGroup",
    "LocationGroupMember",
    "ForecastCache",
    "LLMAudit",
    "ObservationHourly",
    "ForecastHourly",
    "AggregationDaily",
    "ForecastAccuracy",
    "TrendCache",
    "AnalyticsQueryAudit",
    "ProviderRun",
    "AirQualityHourly",
    "AstronomyDaily",
    "DigestAudit",
    # RAG models (new + legacy aliases)
    "Document",
    "DocumentChunk",
    "RagDocument",
    "RagDocumentChunk",
]
