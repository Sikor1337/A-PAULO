"""Request and response schemas for recruitment."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

FieldType = Literal[
    "text", "textarea", "email", "tel", "date", "select", "radio", "checkbox"
]


class RecruitmentFieldCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=250)
    field_type: FieldType = "text"
    required: bool = False
    placeholder: str = Field(default="", max_length=250)
    options: list[str] = Field(default_factory=list)
    position: int | None = Field(default=None, ge=0)


class RecruitmentFieldUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=250)
    field_type: FieldType | None = None
    required: bool | None = None
    placeholder: str | None = Field(default=None, max_length=250)
    options: list[str] | None = None
    position: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class RecruitmentFieldResponse(BaseModel):
    id: int
    key: str
    label: str
    field_type: str
    required: bool
    placeholder: str
    options: list[str]
    position: int
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecruitmentFormResponse(BaseModel):
    title: str = "Formularz rekrutacyjny A PAULO"
    description: str = "Wypełnij formularz, aby zgłosić się do wolontariatu."
    fields: list[RecruitmentFieldResponse]


class RecruitmentPublicFormResponse(RecruitmentFormResponse):
    invitation_token: str
    recipient_name: str | None = None
    recipient_email: str | None = None
    return_reason: str | None = None


class RecruitmentInvitationCreate(BaseModel):
    recipient_name: str | None = Field(default=None, max_length=200)
    recipient_email: EmailStr | None = Field(default=None, max_length=255)


class RecruitmentInvitationResponse(BaseModel):
    id: int
    token: str
    recipient_name: str | None
    recipient_email: str | None
    is_active: bool
    submission_id: int | None
    submission_status: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecruitmentFieldOrderRequest(BaseModel):
    field_ids: list[int] = Field(..., min_length=1)


class RecruitmentSubmissionCreate(BaseModel):
    answers: dict[str, Any]


class RecruitmentAnswerResponse(BaseModel):
    key: str
    label: str
    field_type: str
    value: Any = None


class RecruitmentSubmissionResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    social_link: str
    availability: str
    answers: list[RecruitmentAnswerResponse]
    status: str
    return_reason: str | None
    volunteer_id: int | None
    submitted_at: datetime
    status_changed_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReturnSubmissionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)
