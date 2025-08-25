from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.redis_client import ping_redis
from app.db.database import engine
from app.schemas.dto import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with actual service connectivity tests."""
    
    # Check database connectivity
    database_status = "disconnected"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception as e:
        database_status = f"error: {str(e)[:100]}"
    
    # Check Redis connectivity
    redis_status = "unavailable"
    try:
        if await ping_redis():
            redis_status = "connected"
        else:
            redis_status = "disconnected"
    except Exception as e:
        redis_status = f"error: {str(e)[:100]}"
    
    # Determine overall health status
    overall_status = "healthy"
    if database_status != "connected":
        overall_status = "degraded"
    if redis_status.startswith("error"):
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        timestamp=datetime.utcnow(),
        services={
            "database": database_status,
            "redis": redis_status,
            "openai": "configured" if settings.openai_api_key else "mock_mode"
        }
    )
