"""Beneficiary schemas for PI domain."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.pi.constants import PHONE_MAX_LENGTH
from app.modules.pi.models.enums import BeneficiaryStatus


class BeneficiaryCreateRequest(BaseModel):
    """Beneficiary creation request."""

    full_name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=500)
    phone: str | None = Field(None, max_length=PHONE_MAX_LENGTH)
    family_phone: str | None = Field(None, max_length=PHONE_MAX_LENGTH)
    description: str = Field(default="")
    group_id: int | None = Field(None, alias="group")
    status: BeneficiaryStatus = BeneficiaryStatus.OBECNY
    bo_enrolled: bool = Field(default=False)
    last_priest_visit: date | None = None
    last_volunteer_meeting: date | None = None
    history: str = Field(default="")

    model_config = ConfigDict(populate_by_name=True)


class BeneficiaryUpdateRequest(BaseModel):
    """Beneficiary update request."""

    full_name: str | None = Field(None, min_length=1, max_length=200)
    address: str | None = Field(None, min_length=1, max_length=500)
    phone: str | None = Field(None, max_length=PHONE_MAX_LENGTH)
    family_phone: str | None = Field(None, max_length=PHONE_MAX_LENGTH)
    description: str | None = None
    group_id: int | None = Field(None, alias="group")
    status: BeneficiaryStatus | None = None
    bo_enrolled: bool | None = None
    last_priest_visit: date | None = None
    last_volunteer_meeting: date | None = None
    history: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class BeneficiaryResponse(BaseModel):
    """Beneficiary response DTO."""

    id: int
    full_name: str
    address: str
    phone: str | None
    family_phone: str | None
    description: str
    group_id: int | None = Field(None, alias="group")
    group_name: str | None = None
    status: str
    bo_enrolled: bool
    last_priest_visit: date | None
    last_volunteer_meeting: date | None
    history: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
