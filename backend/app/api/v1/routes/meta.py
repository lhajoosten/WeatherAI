"""Meta configuration API endpoints."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.settings import settings

logger = structlog.get_logger(__name__)

router = APIRouter()


class AnalyticsConfig(BaseModel):
    """Analytics configuration."""
    max_range_days: int


class FeatureFlags(BaseModel):
    """Feature flags configuration."""
    pass  # Placeholder for future feature flags


class ConfigResponse(BaseModel):
    """Configuration response model."""
    analytics: AnalyticsConfig
    feature_flags: FeatureFlags


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get application configuration for frontend."""
    logger.info("Fetching application configuration", action="config.fetch")

    config = ConfigResponse(
        analytics=AnalyticsConfig(
            max_range_days=settings.analytics_max_range_days
        ),
        feature_flags=FeatureFlags()
    )

    logger.info(
        "Configuration fetched successfully",
        action="config.fetch",
        status="success",
        analytics_max_range_days=settings.analytics_max_range_days
    )

    return config
