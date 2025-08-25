
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    check_rate_limit,
    get_current_user,
    get_explain_service,
    get_location_repository,
)
from app.infrastructure.db.models import User
from app.infrastructure.db import LocationRepository
from app.schemas.dto import (
    ExplainResponse,
    LocationCreate,
    LocationResponse,
    LocationUpdate,
)
from app.services.explain_service import ExplainService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
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


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    location_data: LocationUpdate,
    current_user: User = Depends(get_current_user),
    location_repo: LocationRepository = Depends(get_location_repository)
):
    """Update an existing location for the current user."""
    await check_rate_limit("locations_update", current_user)

    # Filter out None values from update data
    update_data = {k: v for k, v in location_data.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid update fields provided"
        )

    location = await location_repo.update(location_id, current_user.id, **update_data)

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    return LocationResponse.from_orm(location)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    location_repo: LocationRepository = Depends(get_location_repository)
):
    """Delete a location for the current user."""
    await check_rate_limit("locations_delete", current_user)

    success = await location_repo.delete(location_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Return 204 No Content (no response body)


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
