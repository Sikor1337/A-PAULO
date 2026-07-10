"""Department schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreateRequest(BaseModel):
    """Department creation request."""

    name: str = Field(..., min_length=1, max_length=200)
    icon: str = Field(default="", max_length=16)
    description: str = Field(default="")


class DepartmentUpdateRequest(BaseModel):
    """Department update request; is_archived toggles archiving."""

    name: str | None = Field(None, min_length=1, max_length=200)
    icon: str | None = Field(None, max_length=16)
    description: str | None = None
    is_archived: bool | None = None


class DepartmentListItem(BaseModel):
    """Department list row with member count."""

    id: int
    name: str
    icon: str
    description: str
    is_archived: bool
    member_count: int

    model_config = ConfigDict(from_attributes=True)


class DepartmentMemberResponse(BaseModel):
    """A volunteer belonging to a department.

    `status` is the volunteer's own status (Aktywny/Były); `membership_status`
    is the department membership lifecycle (PENDING/ACTIVE, PAP-91).
    """

    id: int
    volunteer_id: int
    full_name: str
    email: str
    status: str
    membership_status: str
    created_at: datetime


class DepartmentDetailResponse(BaseModel):
    """Department detail with the member list."""

    id: int
    name: str
    icon: str
    description: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    members: list[DepartmentMemberResponse]


class MemberAddRequest(BaseModel):
    """Add a volunteer to a department."""

    volunteer_id: int
