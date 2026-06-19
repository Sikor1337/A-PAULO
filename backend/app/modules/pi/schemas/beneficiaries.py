"""Beneficiary schemas for PI domain."""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BeneficiaryCreateRequest(BaseModel):
    """Beneficiary creation request."""

    full_name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    family_phone: Optional[str] = Field(None, max_length=20)
    description: str = Field(default="")
    group_id: Optional[int] = Field(None, alias="group")
    status: str = Field(default="OBECNY")
    bo_enrolled: bool = Field(default=False)
    last_priest_visit: Optional[date] = None
    last_volunteer_meeting: Optional[date] = None
    history: str = Field(default="")

    model_config = ConfigDict(populate_by_name=True)


class BeneficiaryUpdateRequest(BaseModel):
    """Beneficiary update request."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    family_phone: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    group_id: Optional[int] = Field(None, alias="group")
    status: Optional[str] = None
    bo_enrolled: Optional[bool] = None
    last_priest_visit: Optional[date] = None
    last_volunteer_meeting: Optional[date] = None
    history: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class BeneficiaryResponse(BaseModel):
    """Beneficiary response DTO."""

    id: int
    full_name: str
    address: str
    phone: Optional[str]
    family_phone: Optional[str]
    description: str
    group_id: Optional[int] = Field(None, alias="group")
    group_name: Optional[str] = None
    status: str
    bo_enrolled: bool
    last_priest_visit: Optional[date]
    last_volunteer_meeting: Optional[date]
    history: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
