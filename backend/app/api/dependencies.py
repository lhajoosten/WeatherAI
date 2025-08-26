
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models import User
from app.infrastructure.db import (
    UserRepository,
    LocationRepository,
    ForecastCacheRepository,
    LLMAuditRepository,
    UserProfileRepository,
    UserPreferencesRepository,
    RagDocumentRepository,
)

# Updated imports - using infrastructure and application layers  
from app.infrastructure.ai.llm.client import LLMClient, create_llm_client
from app.infrastructure.observability.rate_limit import rate_limiter
from app.infrastructure.ai.rag.pipeline import RAGPipeline
from app.infrastructure.cache.service import CacheHelper
from app.application.rag_use_cases import AskRAGQuestion, IngestDocument, RetrieveDocuments
from app.application.weather_use_cases import ExplainWeatherUseCase, GenerateDigestUseCase
# from app.infrastructure.db.rag import RagDocumentRepository
from app.infrastructure.db.base import get_uow
from app.infrastructure.external.auth_service import AuthService

# Legacy imports - to be removed after migration
from app.infrastructure.weather.digest.providers import (
    DatabaseForecastProvider,
    DatabasePreferencesProvider,
    EnhancedLocationService,
)
# RAGService removed; tests and callers should migrate to use cases directly

security = HTTPBearer()

# Global RAG pipeline instance - consider moving to proper dependency injection in production
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


# get_rag_service removed with legacy RAGService elimination


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get user repository."""
    return UserRepository(db)


async def get_location_repository(db: AsyncSession = Depends(get_db)) -> LocationRepository:
    """Get location repository."""
    return LocationRepository(db)


async def get_forecast_repository(db: AsyncSession = Depends(get_db)) -> ForecastCacheRepository:
    """Get forecast cache repository (legacy)."""
    return ForecastCacheRepository(db)


async def get_llm_audit_repository(db: AsyncSession = Depends(get_db)) -> LLMAuditRepository:
    """Get LLM audit repository."""
    return LLMAuditRepository(db)


async def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    """Get auth service."""
    return AuthService(user_repo)


async def get_llm_client(audit_repo: LLMAuditRepository = Depends(get_llm_audit_repository)):
    """Get LLM client."""
    return create_llm_client(audit_repo)



async def get_explain_weather_use_case(
    llm_client: LLMClient = Depends(get_llm_client),
    forecast_repo: ForecastCacheRepository = Depends(get_forecast_repository)
) -> ExplainWeatherUseCase:
    """Get ExplainWeatherUseCase."""
    return ExplainWeatherUseCase(
        llm_client=llm_client,
        forecast_repository=forecast_repo
    )


async def get_cache_service() -> CacheHelper:
    """Get cache service."""
    return CacheHelper(prefix="weather", default_ttl=3600)


async def get_digest_use_case(
    llm_client: LLMClient = Depends(get_llm_client),
    cache_service: CacheHelper = Depends(get_cache_service),
    db: AsyncSession = Depends(get_db)
) -> GenerateDigestUseCase:
    """Get GenerateDigestUseCase."""
    # These are still using the old providers during migration
    # NOTE: Legacy providers expect a session; pass it until refactored
    forecast_provider = DatabaseForecastProvider(db)
    preferences_provider = DatabasePreferencesProvider(db)
    location_service = EnhancedLocationService(db)
    
    return GenerateDigestUseCase(
        forecast_provider=forecast_provider,
        preferences_provider=preferences_provider,
        location_service=location_service,
        llm_client=llm_client,
        cache_service=cache_service
    )


async def get_rag_document_repository(db: AsyncSession = Depends(get_db)) -> RagDocumentRepository:
    """Get RAG document repository."""
    return RagDocumentRepository(db)


async def get_ask_rag_question_use_case(
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    document_repo: RagDocumentRepository = Depends(get_rag_document_repository)
) -> AskRAGQuestion:
    """Get AskRAGQuestion use case."""
    return AskRAGQuestion(rag_pipeline, document_repo, get_uow)


async def get_ingest_document_use_case(
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    document_repo: RagDocumentRepository = Depends(get_rag_document_repository)
) -> IngestDocument:
    """Get IngestDocument use case."""
    return IngestDocument(rag_pipeline, document_repo, get_uow)


async def get_retrieve_documents_use_case(
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    document_repo: RagDocumentRepository = Depends(get_rag_document_repository)
) -> RetrieveDocuments:
    """Get RetrieveDocuments use case."""
    return RetrieveDocuments(document_repo, get_uow)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user."""
    return await auth_service.get_current_user(credentials.credentials)


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    auth_service: AuthService = Depends(get_auth_service)
) -> User | None:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return await auth_service.get_current_user(credentials.credentials)
    except HTTPException:
        return None


async def check_rate_limit(
    endpoint: str,
    user: User | None = None
):
    """Check rate limit for endpoint."""
    # Extract primitive user id; fallback None if not available (typing ignore due to SQLAlchemy instrumentation)
    user_id_obj = getattr(user, 'id', None)
    try:  # type: ignore
        user_id = int(user_id_obj) if user_id_obj is not None else None  # type: ignore
    except Exception:  # pragma: no cover
        user_id = None
    await rate_limiter.check_rate_limit(user_id, endpoint)


async def get_user_profile_repository(db: AsyncSession = Depends(get_db)) -> UserProfileRepository:
    """Get user profile repository."""
    return UserProfileRepository(db)


async def get_user_preferences_repository(db: AsyncSession = Depends(get_db)) -> UserPreferencesRepository:
    """Get user preferences repository."""
    return UserPreferencesRepository(db)
