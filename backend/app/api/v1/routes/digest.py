"""Digest API routes for morning weather digest endpoints.

This module provides the REST API endpoints for retrieving and regenerating
morning weather digests with real data integration and enhanced functionality.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.api.dependencies import check_rate_limit, get_current_user
from app.core.exceptions import (
    DigestGenerationError,
    ForecastUnavailableError,
    InvalidDateFormatError,
    UserPreferencesError,
)
from app.infrastructure.db.database import get_db
from app.infrastructure.db.models import User
from app.infrastructure.db import LLMAuditRepository
from app.schemas.digest import DigestResponse
from app.services.digest_real_providers import (
    DatabaseForecastProvider,
    DatabasePreferencesProvider,
    EnhancedLocationService,
)
from app.services.digest_service import DigestService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/digest", tags=["digest"])


async def get_digest_service(session = Depends(get_db)) -> DigestService:
    """Dependency to get digest service with real providers and LLM integration.

    This creates a fully-featured digest service with:
    - Real database-backed forecast and preferences providers
    - LLM audit repository for audit logging
    - Enhanced location service for user location resolution
    """
    # Create real providers using database session
    forecast_provider = DatabaseForecastProvider(session)
    preferences_provider = DatabasePreferencesProvider(session)
    location_service = EnhancedLocationService(session)

    # Create LLM audit repository for audit logging
    llm_audit_repo = LLMAuditRepository(session)

    # Create service with real providers and LLM enabled by default
    return DigestService(
        forecast_provider=forecast_provider,
        preferences_provider=preferences_provider,
        location_service=location_service,
        llm_audit_repo=llm_audit_repo,
        use_llm=None  # Auto-determine based on audit repo availability
    )


@router.get("/morning", response_model=DigestResponse)
async def get_morning_digest(
    date: str = Query(None, description="Date for digest (YYYY-MM-DD), defaults to today"),
    current_user: User = Depends(get_current_user),
    digest_service: DigestService = Depends(get_digest_service)
) -> DigestResponse:
    """Get morning weather digest for the specified date.

    Retrieves a cached digest if available, otherwise generates a new one.
    The digest includes weather summary, derived metrics, activity recommendations,
    and cache metadata.

    Args:
        date: Optional date string (YYYY-MM-DD). Defaults to today if not provided.
        current_user: Authenticated user (injected by dependency)
        digest_service: Digest service instance (injected by dependency)

    Returns:
        DigestResponse with weather digest and metadata

    Raises:
        400: Invalid date format
        503: Forecast data unavailable
        500: Internal server error during generation
    """
    # Apply rate limiting for digest endpoints
    await check_rate_limit("digest", current_user)

    logger.info(
        "Morning digest requested",
        action="digest_api.get_morning",
        user_id=current_user.id,
        date=date
    )

    try:
        digest = await digest_service.get_morning_digest(
            user_id=str(current_user.id),
            date=date,
            force=False
        )

        logger.info(
            "Morning digest retrieved successfully",
            action="digest_api.get_morning_success",
            user_id=current_user.id,
            date=digest.date,
            cache_hit=digest.cache_meta.hit
        )

        return digest

    except InvalidDateFormatError as e:
        logger.warning(
            "Invalid date format provided",
            action="digest_api.get_morning_error",
            user_id=current_user.id,
            date=date,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=e.message) from e

    except ForecastUnavailableError as e:
        logger.error(f"Forecast unavailable: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from e

    except (UserPreferencesError, DigestGenerationError) as e:
        logger.error(f"Digest generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    except Exception as e:
        logger.exception("Internal server error while generating digest")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/morning", response_model=DigestResponse)
async def regenerate_morning_digest(
    force: bool = Query(True, description="Force regeneration, bypassing cache"),
    date: str = Query(None, description="Date for digest (YYYY-MM-DD), defaults to today"),
    current_user: User = Depends(get_current_user),
    digest_service: DigestService = Depends(get_digest_service)
) -> DigestResponse:
    """Force regeneration of morning weather digest.

    Bypasses cache and generates a fresh digest for the specified date.
    Useful for testing or when user preferences have changed.

    Args:
        force: Force regeneration flag (defaults to True)
        date: Optional date string (YYYY-MM-DD). Defaults to today if not provided.
        current_user: Authenticated user (injected by dependency)
        digest_service: Digest service instance (injected by dependency)

    Returns:
        DigestResponse with freshly generated weather digest

    Raises:
        400: Invalid date format
        503: Forecast data unavailable
        500: Internal server error during generation
    """
    # Apply rate limiting for digest endpoints
    await check_rate_limit("digest", current_user)

    logger.info(
        "Morning digest regeneration requested",
        action="digest_api.regenerate_morning",
        user_id=current_user.id,
        date=date,
        force=force
    )

    try:
        digest = await digest_service.get_morning_digest(
            user_id=str(current_user.id),
            date=date,
            force=force
        )

        logger.info(
            "Morning digest regenerated successfully",
            action="digest_api.regenerate_morning_success",
            user_id=current_user.id,
            date=digest.date,
            cache_hit=digest.cache_meta.hit
        )

        return digest

    except InvalidDateFormatError as e:
        logger.warning(
            "Invalid date format provided",
            action="digest_api.regenerate_morning_error",
            user_id=current_user.id,
            date=date,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=e.message) from e

    except ForecastUnavailableError as e:
        logger.error(f"Forecast unavailable: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from e

    except (UserPreferencesError, DigestGenerationError) as e:
        logger.error(f"Digest generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    except Exception as e:
        logger.exception("Internal server error while regenerating digest")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/morning/metrics")
async def get_digest_metrics(
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """Get digest metrics for debugging and monitoring.

    This endpoint provides access to digest generation metrics for
    debugging and performance monitoring purposes.

    Args:
        current_user: Authenticated user (injected by dependency)

    Returns:
        JSON response with current metrics
    """
    from app.infrastructure.observability.digest import digest_metrics

    logger.debug(
        "Digest metrics requested",
        action="digest_api.get_metrics",
        user_id=current_user.id
    )

    try:
        metrics = digest_metrics.get_all_metrics()
        return JSONResponse(content={
            "status": "success",
            "metrics": metrics,
            "timestamp": logger.bind().info("Metrics retrieved")  # Use current timestamp
        })

    except Exception as e:
        logger.error(
            "Failed to retrieve digest metrics",
            action="digest_api.get_metrics_error",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics") from e
