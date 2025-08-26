"""API routes for air quality and astronomy data."""
import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.repositories.analytics.air_quality_repository import AirQualityRepository
from app.infrastructure.db.repositories.analytics.astronomy_repository import AstronomyRepository
from app.infrastructure.db.repositories.analytics.provider_run_repository import ProviderRunRepository
from app.api.dependencies import get_current_user, get_db
from app.infrastructure.db.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/air-quality")
async def get_air_quality(
    location_id: int = Query(..., description="Location ID"),
    start: datetime | None = Query(None, description="Start time (ISO format)"),
    end: datetime | None = Query(None, description="End time (ISO format)"),
    limit: int = Query(1000, le=1000, description="Maximum number of records"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Get air quality data for a location within a time period."""

    # Set default time range if not provided (last 14 days)
    if end is None:
        end = datetime.utcnow()
    if start is None:
        start = end - timedelta(days=14)

    # Validate date range (max 14 days)
    if (end - start).days > 14:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 14 days")

    # TODO: Validate location ownership for current_user
    # For now, we'll allow access to all locations

    try:
        air_quality_repo = AirQualityRepository(session)
        records = await air_quality_repo.get_by_location_and_period(
            location_id=location_id,
            start_time=start,
            end_time=end,
            limit=limit
        )

        return {
            "location_id": location_id,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "count": len(records),
            "data": [
                {
                    "observed_at": record.observed_at.isoformat(),
                    "pm10": record.pm10,
                    "pm2_5": record.pm2_5,
                    "ozone": record.ozone,
                    "no2": record.no2,
                    "so2": record.so2,
                    "pollen_tree": record.pollen_tree,
                    "pollen_grass": record.pollen_grass,
                    "pollen_weed": record.pollen_weed,
                    "source": record.source
                }
                for record in records
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching air quality data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/astronomy/daily")
async def get_astronomy_daily(
    location_id: int = Query(..., description="Location ID"),
    start: datetime | None = Query(None, description="Start date (ISO format)"),
    end: datetime | None = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, le=100, description="Maximum number of records"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Get daily astronomy data for a location within a date period."""

    # Set default date range if not provided (last 90 days)
    if end is None:
        end = datetime.utcnow()
    if start is None:
        start = end - timedelta(days=90)

    # Validate date range (max 90 days)
    if (end - start).days > 90:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")

    # TODO: Validate location ownership for current_user
    # For now, we'll allow access to all locations

    try:
        astronomy_repo = AstronomyRepository(session)
        records = await astronomy_repo.get_by_location_and_period(
            location_id=location_id,
            start_date=start,
            end_date=end,
            limit=limit
        )

        return {
            "location_id": location_id,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "count": len(records),
            "data": [
                {
                    "date": record.date.date().isoformat(),
                    "sunrise_utc": record.sunrise_utc.isoformat() if record.sunrise_utc else None,
                    "sunset_utc": record.sunset_utc.isoformat() if record.sunset_utc else None,
                    "daylight_minutes": record.daylight_minutes,
                    "moon_phase": record.moon_phase,
                    "civil_twilight_start_utc": record.civil_twilight_start_utc.isoformat() if record.civil_twilight_start_utc else None,
                    "civil_twilight_end_utc": record.civil_twilight_end_utc.isoformat() if record.civil_twilight_end_utc else None,
                    "generated_at": record.generated_at.isoformat()
                }
                for record in records
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching astronomy data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/ingest/runs")
async def get_ingestion_runs(
    provider: str | None = Query(None, description="Filter by provider name"),
    status: str | None = Query(None, description="Filter by status (SUCCESS/FAILED/RUNNING)"),
    limit: int = Query(50, le=100, description="Maximum number of records"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Get recent ingestion runs (admin/internal endpoint)."""

    # TODO: Implement proper authorization - for now, all authenticated users can see runs
    # In production, this should be limited to admin users or user's own location runs

    try:
        provider_run_repo = ProviderRunRepository(session)
        runs = await provider_run_repo.get_recent_runs(
            provider=provider,
            status=status,
            limit=limit
        )

        return {
            "count": len(runs),
            "data": [
                {
                    "id": run.id,
                    "provider": run.provider,
                    "run_type": run.run_type,
                    "location_id": run.location_id,
                    "started_at": run.started_at.isoformat(),
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                    "status": run.status,
                    "records_ingested": run.records_ingested,
                    "error_message": run.error_message
                }
                for run in runs
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching ingestion runs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e
