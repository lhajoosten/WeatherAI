from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.dto import LocationCreate, LocationResponse, ExplainResponse
from app.db.repositories import LocationRepository
from app.services.explain_service import ExplainService
from app.api.dependencies import (
    get_location_repository, 
    get_current_user, 
    get_explain_service,
    check_rate_limit
)
from app.db.models import User

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=List[LocationResponse])
async def get_locations(
    current_user: User = Depends(get_current_user),
    location_repo: LocationRepository = Depends(get_location_repository)
):
    """Get all locations for the current user."""
    await check_rate_limit("locations_list", current_user)
    
    locations = await location_repo.get_by_user_id(current_user.id)
    return [LocationResponse.from_orm(location) for location in locations]


@router.post("", response_model=LocationResponse)
async def create_location(
    location_data: LocationCreate,
    current_user: User = Depends(get_current_user),
    location_repo: LocationRepository = Depends(get_location_repository)
):
    """Create a new location for the current user."""
    await check_rate_limit("locations_create", current_user)
    
    location = await location_repo.create(
        user_id=current_user.id,
        name=location_data.name,
        lat=location_data.lat,
        lon=location_data.lon,
        timezone=location_data.timezone
    )
    
    return LocationResponse.from_orm(location)


@router.post("/{location_id}/explain", response_model=ExplainResponse)
async def explain_location_weather(
    location_id: int,
    current_user: User = Depends(get_current_user),
    location_repo: LocationRepository = Depends(get_location_repository),
    explain_service: ExplainService = Depends(get_explain_service)
):
    """Generate AI explanation for location's weather."""
    await check_rate_limit("explain", current_user)
    
    # Verify location belongs to user
    location = await location_repo.get_by_id_and_user(location_id, current_user.id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Generate explanation
    explanation = await explain_service.explain_location_weather(location, current_user.id)
    
    return ExplainResponse(**explanation)