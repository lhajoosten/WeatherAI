from datetime import datetime
from fastapi import APIRouter
from app.schemas.dto import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow(),
        services={
            "database": "connected",  # TODO: Add actual DB health check
            "redis": "unknown",      # TODO: Add Redis health check  
            "openai": "configured" if settings.openai_api_key else "mock_mode"
        }
    )