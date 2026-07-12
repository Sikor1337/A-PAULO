"""Department schemas."""
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


class DepartmentInventoryItemInput(BaseModel):
    """Create or replace one warehouse item."""

    name: str = Field(..., min_length=1, max_length=200)
    location: str = Field(..., min_length=1, max_length=300)
    borrowed_by_volunteer_id: int | None = Field(default=None, ge=1)
    borrowed_at: date | None = None

    @field_validator("name", "location", mode="before")
    @classmethod
    def strip_required_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def borrower_and_date_must_be_set_together(self) -> Self:
        if (self.borrowed_by_volunteer_id is None) != (self.borrowed_at is None):
            raise ValueError("Wolontariusz i data pobrania muszą być ustawione razem")
        return self


class DepartmentInventoryItemResponse(BaseModel):
    id: int
    department_id: int
    name: str
    location: str
    borrowed_by_volunteer_id: int | None
    borrowed_by_volunteer_name: str | None
    borrowed_at: date | None
    created_at: datetime
    updated_at: datetime


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
