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
    function_ids: list[int] = Field(default_factory=list)
    status: str = Field(default="Aktywny")
    join_date: datetime
    notes: str = Field(default="")
    history: str = Field(default="")


class VolunteerUpdateRequest(BaseModel):
    """Volunteer update request."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    social_link: Optional[str] = Field(None, max_length=500)
    function_ids: Optional[list[int]] = None
    status: Optional[str] = None
    join_date: Optional[datetime] = None
    notes: Optional[str] = None
    history: Optional[str] = None


class VolunteerResponse(BaseModel):
    """Volunteer response DTO."""

    id: int
    full_name: str
    email: str
    phone: Optional[str]
    social_link: Optional[str]
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
    led_group: Optional[str] = None
    assigned_groups: str = ""
    main_for_beneficiaries: Optional[list[str]] = None

    model_config = ConfigDict(from_attributes=True)
