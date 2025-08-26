
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.database import get_db
from app.infrastructure.db.models import User
from app.infrastructure.db import (
    ForecastRepository,
    LLMAuditRepository,
    LocationRepository,
    UserPreferencesRepository,
    UserProfileRepository,
    UserRepository,
)
from app.services.auth_service import AuthService
from app.services.explain_service import ExplainService
from app.services.llm_client import create_llm_client
from app.services.rate_limit import rate_limiter
from app.services.rag_service import RAGService
from app.infrastructure.ai.rag.pipeline import RAGPipeline
from app.application.rag_use_cases import AskRAGQuestion, IngestDocument, RetrieveDocuments
from app.infrastructure.db.rag import RagDocumentRepository
from app.infrastructure.db.base import get_uow

security = HTTPBearer()

# Global RAG pipeline instance - consider moving to proper dependency injection in production
_rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


async def get_rag_service() -> RAGService:
    """Get RAG service with pipeline dependency."""
    pipeline = get_rag_pipeline()
    return RAGService(pipeline)


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get user repository."""
    return UserRepository(db)


async def get_location_repository(db: AsyncSession = Depends(get_db)) -> LocationRepository:
    """Get location repository."""
    return LocationRepository(db)


async def get_forecast_repository(db: AsyncSession = Depends(get_db)) -> ForecastRepository:
    """Get forecast repository."""
    return ForecastRepository(db)


async def get_llm_audit_repository(db: AsyncSession = Depends(get_db)) -> LLMAuditRepository:
    """Get LLM audit repository."""
    return LLMAuditRepository(db)


async def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    """Get auth service."""
    return AuthService(user_repo)


async def get_llm_client(audit_repo: LLMAuditRepository = Depends(get_llm_audit_repository)):
    """Get LLM client."""
    return create_llm_client(audit_repo)


async def get_explain_service(
    llm_client = Depends(get_llm_client),
    forecast_repo: ForecastRepository = Depends(get_forecast_repository)
) -> ExplainService:
    """Get explain service."""
    return ExplainService(llm_client, forecast_repo)


async def get_rag_document_repository(db: AsyncSession = Depends(get_db)) -> RagDocumentRepository:
    """Get RAG document repository."""
    return RagDocumentRepository(db)


async def get_ask_rag_question_use_case(
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    document_repo: RagDocumentRepository = Depends(get_rag_document_repository)
) -> AskRAGQuestion:
    """Get AskRAGQuestion use case."""
    return AskRAGQuestion(
        rag_pipeline=rag_pipeline,
        document_repository=document_repo,
        uow_factory=get_uow
    )


async def get_ingest_document_use_case(
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    document_repo: RagDocumentRepository = Depends(get_rag_document_repository)
) -> IngestDocument:
    """Get IngestDocument use case."""
    return IngestDocument(
        rag_pipeline=rag_pipeline,
        document_repository=document_repo,
        uow_factory=get_uow
    )


async def get_retrieve_documents_use_case(
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    document_repo: RagDocumentRepository = Depends(get_rag_document_repository)
) -> RetrieveDocuments:
    """Get RetrieveDocuments use case."""
    return RetrieveDocuments(
        rag_pipeline=rag_pipeline,
        document_repository=document_repo,
        uow_factory=get_uow
    )


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
    user_id = user.id if user else None
    await rate_limiter.check_rate_limit(user_id, endpoint)


async def get_user_profile_repository(db: AsyncSession = Depends(get_db)) -> UserProfileRepository:
    """Get user profile repository."""
    return UserProfileRepository(db)


async def get_user_preferences_repository(db: AsyncSession = Depends(get_db)) -> UserPreferencesRepository:
    """Get user preferences repository."""
    return UserPreferencesRepository(db)
