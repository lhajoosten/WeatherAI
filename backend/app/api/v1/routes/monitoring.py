"""Metrics endpoint for WeatherAI backend.

This module provides Prometheus-compatible metrics endpoint for monitoring
and observability.
"""

from fastapi import APIRouter, Response, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import structlog

from app.core.metrics import get_prometheus_metrics, is_prometheus_enabled

logger = structlog.get_logger(__name__)
security = HTTPBearer(auto_error=False)

router = APIRouter(tags=["monitoring"])


def verify_metrics_auth(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> bool:
    """Verify authentication for metrics endpoint if required.
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        True if authenticated or auth is disabled
        
    Raises:
        HTTPException: If authentication is required but invalid
    """
    # Check if metrics auth is enabled
    metrics_auth_token = os.getenv("METRICS_AUTH_TOKEN")
    
    if not metrics_auth_token:
        # No auth required
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required for metrics endpoint",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.credentials != metrics_auth_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True


@router.get("/metrics")
async def get_metrics(authenticated: bool = Depends(verify_metrics_auth)) -> Response:
    """Get Prometheus metrics.
    
    Returns metrics in Prometheus format for scraping by monitoring systems.
    Requires authentication token if METRICS_AUTH_TOKEN is set.
    
    Returns:
        Response with Prometheus-formatted metrics
        
    Raises:
        HTTPException: If Prometheus metrics are disabled or unavailable
    """
    if not is_prometheus_enabled():
        raise HTTPException(
            status_code=503,
            detail="Prometheus metrics are disabled"
        )
    
    prometheus_metrics = get_prometheus_metrics()
    if not prometheus_metrics:
        raise HTTPException(
            status_code=503,
            detail="Prometheus metrics not available"
        )
    
    try:
        metrics_output = prometheus_metrics.generate_metrics()
        content_type = prometheus_metrics.get_content_type()
        
        return Response(
            content=metrics_output,
            media_type=content_type
        )
        
    except Exception as e:
        logger.error("Failed to generate metrics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to generate metrics"
        )


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.
    
    Simple health check that doesn't require authentication and
    is excluded from observability middleware.
    
    Returns:
        Basic health status
    """
    return {
        "status": "healthy",
        "service": "weatherai-backend"
    }