"""Pydantic contracts for beneficiary recruitment (PAP-90)."""

import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.recruitment.constants import MAX_ANSWERS_JSON_SIZE
from app.modules.recruitment.schemas.recruitment import (
    RecruitmentAnswerResponse,
    RecruitmentFieldDraft,
    RecruitmentFieldResponse,
)


class BeneficiaryRecruitmentFormUpdateRequest(BaseModel):
    fields: list[RecruitmentFieldDraft] = Field(..., min_length=3, max_length=200)


class BeneficiaryRecruitmentFormResponse(BaseModel):
    title: str = "Zgłoszenie osoby potrzebującej pomocy"
    description: str = (
        "Wypełnij formularz, a zespół A PAULO skontaktuje się z osobą zgłaszającą."
    )
    fields: list[RecruitmentFieldResponse]
    form_token: str


class BeneficiaryRecruitmentSubmissionCreate(BaseModel):
    answers: dict[str, Any]
    form_token: str = Field(..., min_length=10, max_length=200)
    website: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def validate_payload_size(self):
        if len(json.dumps(self.answers, ensure_ascii=False)) > MAX_ANSWERS_JSON_SIZE:
            raise ValueError("Formularz zawiera zbyt dużo danych")
        return self


class BeneficiaryRecruitmentSubmissionResponse(BaseModel):
    id: int
    full_name: str
    address: str
    phone: str | None
    reporter_name: str
    reporter_phone: str
    help_needed: str
    answers: list[RecruitmentAnswerResponse]
    status: Literal["NEW", "BENEFICIARY_CREATED", "REJECTED", "ARCHIVED"]
    decision_comment: str | None
    beneficiary_id: int | None
    submitted_at: datetime
    archived_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BeneficiaryRecruitmentDecisionRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class BeneficiaryRecruitmentCreateBeneficiaryRequest(BaseModel):
    group_id: int | None = Field(default=None, ge=1)
