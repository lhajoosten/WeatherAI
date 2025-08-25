"""Location group schemas."""

from datetime import datetime
from pydantic import BaseModel, Field
from .location import LocationResponse


class LocationGroupCreateRequest(BaseModel):
    """Request schema for location group creation."""
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=500)


class LocationGroupResponse(BaseModel):
    """Location group response DTO."""
    id: int
    name: str
    description: str | None
    created_at: datetime
    members: list[LocationResponse] = []
    member_location_ids: list[int] = []  # For frontend convenience

    @classmethod
    def from_orm(cls, group):
        """Create response from ORM object with proper member transformation."""
        # Handle case where members might not be loaded due to lazy='raise'
        try:
            members = [LocationResponse.model_validate(member.location) for member in group.members]
            member_location_ids = [member.location.id for member in group.members]
        except Exception:
            # If members relationship is not loaded, return empty lists
            members = []
            member_location_ids = []

        return cls(
            id=group.id,
            name=group.name,
            description=group.description,
            created_at=group.created_at,
            members=members,
            member_location_ids=member_location_ids
        )

    class Config:
        from_attributes = True


class LocationGroupMemberCreateRequest(BaseModel):
    """Request schema for adding a member to a location group."""
    location_id: int


class LocationGroupBulkMembershipRequest(BaseModel):
    """Bulk membership request for adding/removing multiple locations at once."""
    add: list[int] = Field(default=[], description="Location IDs to add to the group")
    remove: list[int] = Field(default=[], description="Location IDs to remove from the group")


class LocationGroupMemberResponse(BaseModel):
    """Location group member response DTO."""
    id: int
    group_id: int
    location_id: int
    added_at: datetime
    location: LocationResponse

    class Config:
        from_attributes = True