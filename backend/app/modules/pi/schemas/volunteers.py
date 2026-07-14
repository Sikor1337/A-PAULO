"""Volunteer schemas for PI domain."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.pi.constants import PHONE_MAX_LENGTH
from app.modules.pi.models.enums import VolunteerStatus


def validate_polish_phone(phone: str) -> str:
    """Validate Polish phone number format."""
    if phone and not re.match(r"^(?:\+48)?[ \-]?\d{3}[ \-]?\d{3}[ \-]?\d{3}$", phone):
        raise ValueError("Podaj prawidłowy polski numer telefonu (np. +48 123 456 789)")
    return phone


class VolunteerCreateRequest(BaseModel):
    """Volunteer creation request."""

    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(None, max_length=PHONE_MAX_LENGTH)
    social_link: str | None = Field(None, max_length=500)
    function_ids: list[int] = Field(default_factory=list)
    status: VolunteerStatus = VolunteerStatus.AKTYWNY
    join_date: datetime
    notes: str = Field(default="")
    history: str = Field(default="")


class VolunteerUpdateRequest(BaseModel):
    """Volunteer update request."""

    full_name: str | None = Field(None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=PHONE_MAX_LENGTH)
    social_link: str | None = Field(None, max_length=500)
    function_ids: list[int] | None = None
    status: VolunteerStatus | None = None
    join_date: datetime | None = None
    notes: str | None = None
    history: str | None = None


class VolunteerResponse(BaseModel):
    """Volunteer response DTO."""

    id: int
    full_name: str
    email: str
    phone: str | None
    social_link: str | None
    function_ids: list[int] = Field(default_factory=list)
    manual_functions: list[str] = Field(default_factory=list)
    derived_functions: list[str] = Field(default_factory=list)
    functions: list[str] = Field(default_factory=list)
    status: str
    join_date: datetime
    notes: str
    history: str
    created_at: datetime
    updated_at: datetime
    led_group: str | None = None
    assigned_groups: str = ""
    main_for_beneficiaries: list[str] | None = None

    model_config = ConfigDict(from_attributes=True)
