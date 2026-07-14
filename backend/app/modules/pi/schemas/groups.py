"""Group and assignment schemas for PI domain."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# -------------------------
# payload z frontu
# -------------------------


class GroupVolunteerInput(BaseModel):
    id: int
    additional_info: str = ""


class GroupBeneficiaryAssignmentInput(BaseModel):
    beneficiary: int
    volunteers: list[GroupVolunteerInput] = []
    main_volunteer: int | None = None


class GroupCreateRequest(BaseModel):
    """Group creation request."""

    name: str = Field(..., min_length=1, max_length=100)
    leader_id: int | None = Field(default=None, alias="leader")
    assignments: list[GroupBeneficiaryAssignmentInput] = []

    model_config = ConfigDict(populate_by_name=True)


class GroupUpdateRequest(BaseModel):
    """Group update request."""

    name: str | None = Field(None, min_length=1, max_length=100)
    leader_id: int | None = Field(default=None, alias="leader")
    assignments: list[GroupBeneficiaryAssignmentInput] | None = None

    model_config = ConfigDict(populate_by_name=True)


# -------------------------
# list response
# -------------------------


class GroupResponse(BaseModel):
    """Group response DTO."""

    id: int
    name: str
    leader_id: int | None = Field(None, alias="leader")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# -------------------------
# detail response do GroupsPage
# -------------------------


class GroupDetailVolunteerResponse(BaseModel):
    id: int
    full_name: str
    is_main: bool = False
    additional_info: str = ""

    model_config = ConfigDict(from_attributes=True)


class GroupDetailBeneficiaryResponse(BaseModel):
    id: int
    full_name: str
    volunteers: list[GroupDetailVolunteerResponse] = []

    model_config = ConfigDict(from_attributes=True)


class GroupDetailResponse(BaseModel):
    id: int
    name: str
    leader_id: int | None = Field(None, alias="leader")
    leader_name: str | None = None
    beneficiaries: list[GroupDetailBeneficiaryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# -------------------------
# assignments API (osobne endpointy)
# -------------------------


class BeneficiaryAssignmentCreateRequest(BaseModel):
    """Beneficiary assignment creation request."""

    beneficiary_id: int = Field(alias="beneficiary")
    volunteer_id: int = Field(alias="volunteer")
    is_main: bool = Field(default=False)
    additional_info: str = Field(default="")

    model_config = ConfigDict(populate_by_name=True)


class BeneficiaryAssignmentUpdateRequest(BaseModel):
    """Beneficiary assignment update request."""

    is_main: bool | None = None
    additional_info: str | None = None


class BeneficiaryAssignmentResponse(BaseModel):
    """Beneficiary assignment response DTO."""

    id: int
    beneficiary_id: int
    volunteer_id: int
    is_main: bool
    additional_info: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
