
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.db.repositories import (
    ForecastRepository,
    LLMAuditRepository,
    LocationGroupRepository,
    LocationRepository,
    UserRepository,
)
from app.services.auth_service import AuthService
from app.services.explain_service import ExplainService
from app.services.llm_client import create_llm_client
from app.services.rate_limit import rate_limiter

security = HTTPBearer()


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
