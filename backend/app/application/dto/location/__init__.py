"""Location schema models for geographical data management."""

from .location import (
    LocationCreateRequest,
    LocationUpdateRequest,
    LocationResponse,
)
from .location_group import (
    LocationGroupCreateRequest,
    LocationGroupResponse,
    LocationGroupMemberCreateRequest,
    LocationGroupBulkMembershipRequest,
    LocationGroupMemberResponse,
)

__all__ = [
    # Location
    "LocationCreateRequest",
    "LocationUpdateRequest",
    "LocationResponse",
    # Location Groups
    "LocationGroupCreateRequest",
    "LocationGroupResponse",
    "LocationGroupMemberCreateRequest",
    "LocationGroupBulkMembershipRequest", 
    "LocationGroupMemberResponse",
]