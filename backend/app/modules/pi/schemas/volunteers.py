"""Volunteer schemas for PI domain."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
import re


def validate_polish_phone(phone: str) -> str:
    """Validate Polish phone number format."""
    if phone and not re.match(r"^(?:\+48)?[ \-]?\d{3}[ \-]?\d{3}[ \-]?\d{3}$", phone):
        raise ValueError("Podaj prawidłowy polski numer telefonu (np. +48 123 456 789)")
    return phone


class VolunteerCreateRequest(BaseModel):
    """Volunteer creation request."""

    full_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    social_link: Optional[str] = Field(None, max_length=500)
    status: str = Field(default="Aktywny")
    role_id: Optional[int] = Field(default=None, alias="role")
    join_date: datetime
    notes: str = Field(default="")
    history: str = Field(default="")

    model_config = ConfigDict(populate_by_name=True)


class VolunteerUpdateRequest(BaseModel):
    """Volunteer update request."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    social_link: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None
    role_id: Optional[int] = Field(default=None, alias="role")
    join_date: Optional[datetime] = None
    notes: Optional[str] = None
    history: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class VolunteerResponse(BaseModel):
    """Volunteer response DTO."""

    id: int
    full_name: str
    email: str
    phone: Optional[str]
    social_link: Optional[str]
    status: str
    role_id: Optional[int] = Field(None, alias="role")
    role_name: Optional[str] = None
    join_date: datetime
    notes: str
    history: str
    created_at: datetime
    updated_at: datetime
    led_group: Optional[str] = None
    assigned_groups: str = ""
    main_for_beneficiaries: Optional[list[str]] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
