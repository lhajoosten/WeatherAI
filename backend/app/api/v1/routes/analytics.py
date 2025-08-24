import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.repositories.accuracy_repository import AccuracyRepository
from app.analytics.repositories.aggregation_repository import AggregationRepository
from app.analytics.repositories.analytics_audit_repository import (
    AnalyticsAuditRepository,
)
from app.analytics.repositories.observation_repository import ObservationRepository
from app.analytics.repositories.trend_repository import TrendRepository
from app.analytics.services.summary_prompt_service import SummaryPromptService
from app.api.dependencies import get_current_user, get_db
from app.db.models import User
from app.db.repositories import LocationRepository
from app.services.rate_limit import rate_limiter
from app.services.analytics_cache import analytics_cache

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for responses
class ObservationResponse(BaseModel):
    id: int
    location_id: int
    observed_at: datetime
    temp_c: float | None = None
    wind_kph: float | None = None
    precip_mm: float | None = None
    humidity_pct: float | None = None
    condition_code: str | None = None
    source: str

    class Config:
        from_attributes = True


class AggregationResponse(BaseModel):
    id: int
    location_id: int
    date: datetime
    temp_min_c: float | None = None
    temp_max_c: float | None = None
    avg_temp_c: float | None = None
    total_precip_mm: float | None = None
    max_wind_kph: float | None = None
    heating_degree_days: float | None = None
    cooling_degree_days: float | None = None
    generated_at: datetime | None = None

    class Config:
        from_attributes = True


class TrendResponse(BaseModel):
    id: int
    location_id: int
    metric: str
    period: str
    current_value: float | None = None
    previous_value: float | None = None
    delta: float | None = None
    pct_change: float | None = None
    generated_at: datetime | None = None

    class Config:
        from_attributes = True


class AccuracyResponse(BaseModel):
    id: int
    location_id: int
    target_time: datetime
    forecast_issue_time: datetime
    variable: str
    forecast_value: float | None = None
    observed_value: float | None = None
    abs_error: float | None = None
    pct_error: float | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AnalyticsSummaryRequest(BaseModel):
    location_id: int
    period: str = Field(default="7d", pattern="^(7d|30d)$")
    metrics: list[str] = Field(default=["avg_temp_c", "total_precip_mm", "max_wind_kph"])


class AnalyticsSummaryResponse(BaseModel):
    narrative: str | None = None
    model: str
    tokens_in: int
    tokens_out: int
    prompt_version: str
    generated_at: datetime
    reason: str | None = None  # e.g., "NO_DATA" when insufficient data


# Helper function to validate date range
def _validate_date_range(start: str | None, end: str | None, max_days: int = 14) -> tuple[datetime, datetime]:
    """Validate and parse start/end date parameters with range limits."""
    try:
        if start:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        else:
            start_date = datetime.utcnow() - timedelta(days=7)

        if end:
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        else:
            end_date = datetime.utcnow()

        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )

        if (end_date - start_date).days > max_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Date range cannot exceed {max_days} days"
            )

        return start_date, end_date
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        ) from e


# Helper function to log analytics queries
async def _log_analytics_query(
    session: AsyncSession,
    user_id: int | None,
    endpoint: str,
    params: dict[str, Any],
    duration_ms: int,
    rows_returned: int
):
    """Log analytics query for audit purposes."""
    try:
        audit_repo = AnalyticsAuditRepository(session)
        await audit_repo.record(
            user_id=user_id,
            endpoint=endpoint,
            params_json=json.dumps(params, default=str),
            duration_ms=duration_ms,
            rows_returned=rows_returned
        )
    except Exception as e:
        logger.warning(f"Failed to log analytics query: {e}")


@router.get("/observations", response_model=list[ObservationResponse])
async def get_observations(
    location_id: int = Query(..., description="Location ID"),
    start: str | None = Query(None, description="Start time (ISO 8601)"),
    end: str | None = Query(None, description="End time (ISO 8601)"),
    limit: int = Query(1000, le=1000, description="Maximum number of records"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get hourly observations for a location within a date range."""
    start_time = time.time()

    # Rate limiting
    await rate_limiter.check_rate_limit(current_user.id, "analytics")

    # Validate date range
    start_date, end_date = _validate_date_range(start, end, max_days=14)

    # Verify user owns this location
    location_repo = LocationRepository(session)
    location = await location_repo.get_by_id_and_user(location_id, current_user.id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Get data
    observation_repo = ObservationRepository(session)
    try:
        observations = await observation_repo.get_by_location_and_period(
            location_id=location_id,
            start_time=start_date,
            end_time=end_date,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error fetching observations for location {location_id}: {e}")
        # Return empty list instead of 500 error for better UX
        observations = []

    # Log query
    duration_ms = int((time.time() - start_time) * 1000)
    await _log_analytics_query(
        session=session,
        user_id=current_user.id,
        endpoint="observations",
        params={"location_id": location_id, "start": start, "end": end, "limit": limit},
        duration_ms=duration_ms,
        rows_returned=len(observations)
    )

    logger.info(f"Analytics query: observations, user={current_user.id}, location={location_id}, rows={len(observations)}, duration={duration_ms}ms")

    return [ObservationResponse.model_validate(obs) for obs in observations]


@router.get("/aggregations/daily", response_model=list[AggregationResponse])
async def get_daily_aggregations(
    location_id: int = Query(..., description="Location ID"),
    start: str | None = Query(None, description="Start date (ISO 8601)"),
    end: str | None = Query(None, description="End date (ISO 8601)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get daily aggregated weather data for a location."""
    start_time = time.time()

    # Rate limiting
    await rate_limiter.check_rate_limit(current_user.id, "analytics")

    # Validate date range
    start_date, end_date = _validate_date_range(start, end, max_days=90)  # Allow longer range for daily data

    # TODO: Verify user owns this location

    # Get data
    aggregation_repo = AggregationRepository(session)
    aggregations = await aggregation_repo.get_by_location_and_period(
        location_id=location_id,
        start_date=start_date,
        end_date=end_date
    )

    # Log query
    duration_ms = int((time.time() - start_time) * 1000)
    await _log_analytics_query(
        session=session,
        user_id=current_user.id,
        endpoint="aggregations_daily",
        params={"location_id": location_id, "start": start, "end": end},
        duration_ms=duration_ms,
        rows_returned=len(aggregations)
    )

    logger.info(f"Analytics query: aggregations_daily, user={current_user.id}, location={location_id}, rows={len(aggregations)}, duration={duration_ms}ms")

    return [AggregationResponse.model_validate(agg) for agg in aggregations]


@router.get("/trends", response_model=list[TrendResponse])
async def get_trends(
    location_id: int = Query(..., description="Location ID"),
    period: str = Query("30d", description="Period (7d, 30d)"),
    metrics: list[str] = Query(["avg_temp_c", "total_precip_mm", "max_wind_kph"], description="Metrics to include"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get trend analysis for weather metrics."""
    start_time = time.time()

    # Rate limiting
    await rate_limiter.check_rate_limit(current_user.id, "analytics")

    # Validate period
    if period not in ["7d", "30d"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period must be '7d' or '30d'"
        )

    # Validate metrics
    valid_metrics = ["avg_temp_c", "temp_min_c", "temp_max_c", "total_precip_mm", "max_wind_kph", "heating_degree_days", "cooling_degree_days"]
    for metric in metrics:
        if metric not in valid_metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric: {metric}. Valid options: {valid_metrics}"
            )

    # TODO: Verify user owns this location

    # Get data
    trend_repo = TrendRepository(session)
    trends = await trend_repo.get_by_location_and_metrics(
        location_id=location_id,
        period=period,
        metrics=metrics
    )

    # Log query
    duration_ms = int((time.time() - start_time) * 1000)
    await _log_analytics_query(
        session=session,
        user_id=current_user.id,
        endpoint="trends",
        params={"location_id": location_id, "period": period, "metrics": metrics},
        duration_ms=duration_ms,
        rows_returned=len(trends)
    )

    logger.info(f"Analytics query: trends, user={current_user.id}, location={location_id}, rows={len(trends)}, duration={duration_ms}ms")

    return [TrendResponse.model_validate(trend) for trend in trends]


@router.get("/accuracy", response_model=list[AccuracyResponse])
async def get_forecast_accuracy(
    location_id: int = Query(..., description="Location ID"),
    start: str | None = Query(None, description="Start time (ISO 8601)"),
    end: str | None = Query(None, description="End time (ISO 8601)"),
    variables: list[str] = Query(["temp_c", "precipitation_probability_pct"], description="Variables to include"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get forecast accuracy metrics for a location."""
    start_time = time.time()

    # Rate limiting
    await rate_limiter.check_rate_limit(current_user.id, "analytics")

    # Validate date range
    start_date, end_date = _validate_date_range(start, end, max_days=30)

    # Validate variables
    valid_variables = ["temp_c", "precipitation_probability_pct"]
    for variable in variables:
        if variable not in valid_variables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid variable: {variable}. Valid options: {valid_variables}"
            )

    # TODO: Verify user owns this location

    # Get data
    accuracy_repo = AccuracyRepository(session)
    accuracy_records = await accuracy_repo.get_by_location_and_period(
        location_id=location_id,
        start_time=start_date,
        end_time=end_date,
        variables=variables
    )

    # Log query
    duration_ms = int((time.time() - start_time) * 1000)
    await _log_analytics_query(
        session=session,
        user_id=current_user.id,
        endpoint="accuracy",
        params={"location_id": location_id, "start": start, "end": end, "variables": variables},
        duration_ms=duration_ms,
        rows_returned=len(accuracy_records)
    )

    logger.info(f"Analytics query: accuracy, user={current_user.id}, location={location_id}, rows={len(accuracy_records)}, duration={duration_ms}ms")

    return [AccuracyResponse.model_validate(acc) for acc in accuracy_records]


@router.post("/summary", response_model=AnalyticsSummaryResponse)
async def generate_analytics_summary(
    request: AnalyticsSummaryRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Generate AI-powered analytics summary for a location."""
    start_time = time.time()

    # LLM rate limiting (separate limit)
    await rate_limiter.check_rate_limit(current_user.id, "analytics_llm")

    # TODO: Verify user owns this location

    try:
        # Build structured prompt
        prompt_service = SummaryPromptService(session)
        prompt_data = await prompt_service.build_analytics_prompt(
            location_id=request.location_id,
            period=request.period,
            metrics=request.metrics
        )

        # Check if we have sufficient data for analysis
        if not prompt_data['metadata'].get('has_sufficient_data', False):
            logger.info(f"No data available for analytics summary: location={request.location_id}, period={request.period}")
            return AnalyticsSummaryResponse(
                narrative=None,
                model="system",
                tokens_in=0,
                tokens_out=0,
                prompt_version="analytics_summary_v1",
                generated_at=datetime.utcnow(),
                reason="NO_DATA"
            )

        # Format prompt for LLM
        prompt_text = prompt_service.format_prompt_for_llm(prompt_data)

        # Generate summary using LLM client
        from app.db.repositories import LLMAuditRepository
        from app.services.llm_client import create_llm_client

        llm_audit_repo = LLMAuditRepository(session)
        llm_client = create_llm_client(llm_audit_repo)

        if llm_client.openai_client:
            # Real LLM call
            result = await llm_client.generate(
                prompt=prompt_text,
                user_id=current_user.id,
                endpoint="analytics_summary",
                temperature=0.1,  # Low temperature for factual analysis
                max_tokens=500
            )
            narrative = result["text"]
            model = result.get("model", "gpt-4")
            tokens_in = result.get("tokens_in", 0)
            tokens_out = result.get("tokens_out", 0)
        else:
            # Mock response when no OpenAI key
            narrative = f"""Overview: Analysis of {request.period} weather data for location {request.location_id} shows mixed patterns across monitored metrics.

Notable Changes: Temperature trends indicate seasonal variation within expected ranges. Precipitation levels remain consistent with historical averages.

Accuracy: Forecast models demonstrate reasonable performance for temperature predictions. Precipitation probability forecasts show typical accuracy levels for the period.

Actions: Monitor upcoming weather patterns for potential changes. Consider seasonal adjustments to weather-dependent activities. Review forecast accuracy trends for planning purposes."""
            model = "mock"
            tokens_in = len(prompt_text.split())
            tokens_out = len(narrative.split())

        # Log query
        duration_ms = int((time.time() - start_time) * 1000)
        await _log_analytics_query(
            session=session,
            user_id=current_user.id,
            endpoint="summary",
            params={"location_id": request.location_id, "period": request.period, "metrics": request.metrics},
            duration_ms=duration_ms,
            rows_returned=1
        )

        logger.info(f"Analytics summary generated: user={current_user.id}, location={request.location_id}, model={model}, tokens_in={tokens_in}, tokens_out={tokens_out}")

        return AnalyticsSummaryResponse(
            narrative=narrative,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            prompt_version="analytics_summary_v1",
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.exception(f"Failed to generate analytics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analytics summary"
        )


class DashboardResponse(BaseModel):
    """Combined dashboard response with all analytics data."""
    observations: list[ObservationResponse]
    aggregations: list[AggregationResponse] 
    trends: list[dict[str, Any]]
    accuracy: dict[str, Any]
    generated_at: datetime
    cache_hit: bool = False


@router.get("/{location_id}/dashboard", response_model=DashboardResponse)
async def get_dashboard_analytics(
    location_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=24, le=100)
):
    """Get consolidated dashboard analytics for a location."""
    # Use consolidated rate limiting for dashboard
    await rate_limiter.check_rate_limit(current_user.id, "analytics")
    
    # Verify location ownership
    location_repo = LocationRepository(session)
    location = await location_repo.get_by_id_and_user(location_id, current_user.id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check cache first (simple in-memory cache for identical requests)
    cache_key_params = {'limit': limit}
    cached_result = analytics_cache.get(location_id, 'dashboard', **cache_key_params)
    if cached_result:
        cached_result.cache_hit = True
        return cached_result
    
    try:
        # Collect all data in parallel 
        observation_repo = ObservationRepository(session)
        aggregation_repo = AggregationRepository(session)
        trend_repo = TrendRepository(session)
        accuracy_repo = AccuracyRepository(session)
        
        # Get recent observations (last 24 hours by default)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=limit)
        
        observations = await observation_repo.get_by_location_and_period(
            location_id=location_id,
            start_time=start_time,
            end_time=end_time
        )
        
        # Get daily aggregations (last 7 days)
        agg_end_date = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
        agg_start_date = agg_end_date - timedelta(days=7)
        
        aggregations = await aggregation_repo.get_by_location_and_period(
            location_id=location_id,
            start_date=agg_start_date,
            end_date=agg_end_date
        )
        
        # Get trends (7-day period)
        trends = await trend_repo.get_by_location_and_metrics(
            location_id=location_id,
            period='7d',
            metrics=['avg_temp_c', 'total_precip_mm', 'max_wind_kph']
        )
        
        # Get accuracy summary
        accuracy_records = await accuracy_repo.get_by_location_and_period(
            location_id=location_id,
            start_time=agg_start_date,
            end_time=agg_end_date,
            variables=['temp_c', 'precipitation_probability_pct']
        )
        
        # Build accuracy summary
        accuracy_summary = {}
        if accuracy_records:
            for variable in ['temp_c', 'precipitation_probability_pct']:
                var_records = [r for r in accuracy_records if r.variable == variable and r.abs_error is not None]
                if var_records:
                    avg_abs_error = sum(r.abs_error for r in var_records) / len(var_records)
                    accuracy_summary[variable] = {
                        "sample_size": len(var_records),
                        "avg_absolute_error": round(avg_abs_error, 2)
                    }
        
        # Convert trends to dict format
        trends_data = [
            {
                "metric": trend.metric,
                "period": trend.period,
                "current_value": trend.current_value,
                "previous_value": trend.previous_value,
                "delta": trend.delta,
                "pct_change": round(trend.pct_change, 1) if trend.pct_change else None
            }
            for trend in trends
        ]
        
        result = DashboardResponse(
            observations=[ObservationResponse.model_validate(obs) for obs in observations],
            aggregations=[AggregationResponse.model_validate(agg) for agg in aggregations],
            trends=trends_data,
            accuracy=accuracy_summary,
            generated_at=datetime.utcnow(),
            cache_hit=False
        )
        
        # Cache the result
        analytics_cache.set(location_id, 'dashboard', result, ttl=15, **cache_key_params)
        
        return result
        
    except Exception as e:
        logger.exception(f"Failed to get dashboard analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard analytics"
        )
