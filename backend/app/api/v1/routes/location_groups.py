from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    check_rate_limit,
    get_current_user,
    get_db,
)
from app.db.models import User
from app.db.repositories import LocationGroupRepository
from app.schemas.dto import (
    LocationGroupCreate,
    LocationGroupResponse,
    LocationGroupMemberCreate,
    LocationGroupMemberResponse,
    LocationGroupBulkMembershipRequest,
)

router = APIRouter(prefix="/location-groups", tags=["location-groups"])


async def get_location_group_repository(
    session=Depends(get_db),
) -> LocationGroupRepository:
    """Dependency to get LocationGroupRepository."""
    return LocationGroupRepository(session)


@router.get("", response_model=list[LocationGroupResponse])
async def get_location_groups(
    current_user: User = Depends(get_current_user),
    group_repo: LocationGroupRepository = Depends(get_location_group_repository),
):
    """Get all location groups for the current user."""
    await check_rate_limit("location_groups_list", current_user)

    groups = await group_repo.get_by_user_id(current_user.id)
    return [LocationGroupResponse.from_orm(group) for group in groups]


@router.post("", response_model=LocationGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_location_group(
    group_data: LocationGroupCreate,
    current_user: User = Depends(get_current_user),
    group_repo: LocationGroupRepository = Depends(get_location_group_repository),
):
    """Create a new location group for the current user."""
    await check_rate_limit("location_groups_create", current_user)

    group = await group_repo.create(
        user_id=current_user.id,
        name=group_data.name,
        description=group_data.description,
    )

    # Return DTO assembled from known values (new groups have no members)
    return LocationGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        members=[],
        member_location_ids=[]
    )


@router.post("/{group_id}/locations", response_model=LocationGroupResponse)
async def add_location_to_group(
    group_id: int,
    member_data: LocationGroupMemberCreate,
    current_user: User = Depends(get_current_user),
    group_repo: LocationGroupRepository = Depends(get_location_group_repository),
):
    """Add a location to a group."""
    await check_rate_limit("location_groups_add_member", current_user)

    member = await group_repo.add_member(
        group_id=group_id,
        location_id=member_data.location_id,
        user_id=current_user.id,
    )

    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add location to group. Group or location not found, or location already in group.",
        )

    # Return updated group with members
    updated_group = await group_repo.get_by_id_and_user(group_id, current_user.id)
    return LocationGroupResponse.from_orm(updated_group)


@router.delete("/{group_id}/locations/{location_id}", response_model=LocationGroupResponse)
async def remove_location_from_group(
    group_id: int,
    location_id: int,
    current_user: User = Depends(get_current_user),
    group_repo: LocationGroupRepository = Depends(get_location_group_repository),
):
    """Remove a location from a group."""
    await check_rate_limit("location_groups_remove_member", current_user)

    success = await group_repo.remove_member(
        group_id=group_id,
        location_id=location_id,
        user_id=current_user.id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group or location membership not found",
        )

    # Return updated group with members
    updated_group = await group_repo.get_by_id_and_user(group_id, current_user.id)
    return LocationGroupResponse.from_orm(updated_group)


@router.post("/{group_id}/members/bulk", response_model=LocationGroupResponse)
async def bulk_update_group_members(
    group_id: int,
    bulk_request: LocationGroupBulkMembershipRequest,
    current_user: User = Depends(get_current_user),
    group_repo: LocationGroupRepository = Depends(get_location_group_repository),
):
    """Bulk add/remove locations to/from a group."""
    await check_rate_limit("location_groups_bulk_members", current_user)

    updated_group = await group_repo.bulk_update_members(
        group_id=group_id,
        user_id=current_user.id,
        add_location_ids=bulk_request.add,
        remove_location_ids=bulk_request.remove,
    )

    if not updated_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location group not found",
        )

    return LocationGroupResponse.from_orm(updated_group)


@router.delete("/{group_id}")
async def delete_location_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    group_repo: LocationGroupRepository = Depends(get_location_group_repository),
):
    """Delete a location group."""
    await check_rate_limit("location_groups_delete", current_user)

    success = await group_repo.delete(group_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location group not found",
        )

    return {"message": "Location group deleted successfully"}