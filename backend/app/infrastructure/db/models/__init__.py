"""Database models package."""

# Import domain bases
from .core import CoreBase
from .rag import RagBase, Document, DocumentChunk

# Legacy import for backward compatibility - import from the parent models.py
import importlib.util
from pathlib import Path

# Load the Base from the models.py file at the db level
models_file = Path(__file__).parent.parent / "models.py"
spec = importlib.util.spec_from_file_location("legacy_models", models_file)
legacy_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy_models)

# Re-export all legacy models for backward compatibility
Base = legacy_models.Base
User = legacy_models.User
UserProfile = legacy_models.UserProfile
UserPreferences = legacy_models.UserPreferences
Location = legacy_models.Location
LocationGroup = legacy_models.LocationGroup
LocationGroupMember = legacy_models.LocationGroupMember
LLMAudit = legacy_models.LLMAudit
ForecastCache = legacy_models.ForecastCache
ObservationHourly = legacy_models.ObservationHourly
ForecastHourly = legacy_models.ForecastHourly
AggregationDaily = legacy_models.AggregationDaily
ForecastAccuracy = legacy_models.ForecastAccuracy
TrendCache = legacy_models.TrendCache
AnalyticsQueryAudit = legacy_models.AnalyticsQueryAudit
ProviderRun = legacy_models.ProviderRun
AirQualityHourly = legacy_models.AirQualityHourly
AstronomyDaily = legacy_models.AstronomyDaily
DigestAudit = legacy_models.DigestAudit
RagDocument = legacy_models.RagDocument
RagDocumentChunk = legacy_models.RagDocumentChunk

# Export new RAG models for external use
__all__ = [
    # Legacy models (for backward compatibility)
    "Base",
    "User",
    "UserProfile", 
    "UserPreferences",
    "Location",
    "LocationGroup",
    "LocationGroupMember",
    "LLMAudit",
    "ForecastCache",
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
    "RagDocument",
    "RagDocumentChunk",
    # New domain models
    "CoreBase",
    "RagBase",
    "Document",
    "DocumentChunk",
]