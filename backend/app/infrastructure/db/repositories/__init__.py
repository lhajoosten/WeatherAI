"""Repository package exports.

This aggregates individual repository modules for convenient importing.
"""

from .user_repository import UserRepository
from .user_profile_repository import UserProfileRepository
from .user_preferences_repository import UserPreferencesRepository
from .location_repository import LocationRepository
from .location_group_repository import LocationGroupRepository
from .forecast_cache_repository import ForecastCacheRepository
from .llm_audit_repository import LLMAuditRepository
from .rag_document_repository import RagDocumentRepository

# Analytics / domain specific repositories (already modularized)
from .observation_repository import ObservationRepository
from .forecast_repository import ForecastRepository  # ForecastHourly analytics
from .aggregation_repository import AggregationRepository
from .accuracy_repository import AccuracyRepository
from .trend_repository import TrendRepository
from .analytics_audit_repository import AnalyticsAuditRepository
from .provider_run_repository import ProviderRunRepository
from .air_quality_repository import AirQualityRepository
from .astronomy_repository import AstronomyRepository

__all__ = [
	"UserRepository",
	"UserProfileRepository",
	"UserPreferencesRepository",
	"LocationRepository",
	"LocationGroupRepository",
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
]

