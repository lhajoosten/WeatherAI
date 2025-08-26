import subprocess
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.redis_client import ping_redis
from app.infrastructure.db.database import engine
from app.application.dto.dto import HealthResponse

router = APIRouter(tags=["health"])


async def get_database_status() -> dict:
    """Get database connection status and migration version."""
    try:
        from sqlalchemy import text

        from app.infrastructure.db.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

            # Try to get migration version
            try:
                result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                version_row = result.fetchone()
                migration_version = version_row[0] if version_row else "unknown"
            except Exception:
                migration_version = "no_alembic_table"

            return {
                "status": "connected",
                "migration_version": migration_version
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_app_version() -> str:
    """Get application version from git or fallback."""
    try:
        # Try to get git commit hash
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return f"git-{result.stdout.strip()}"
    except Exception:
        pass

    return "0.1.0"


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
            "openai": {
                "status": "configured" if settings.openai_api_key else "mock_mode",
                "model": settings.openai_model
            }

        }
    )
