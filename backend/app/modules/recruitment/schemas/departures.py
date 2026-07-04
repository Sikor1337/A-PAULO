"""API schemas for volunteer departure interviews."""

import json
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DepartureFieldType = Literal[
    "text", "textarea", "date", "select", "radio", "multiselect", "checkbox"
]


class DepartureFieldDraft(BaseModel):
    id: int | None = Field(default=None, ge=1)
    label: str = Field(..., min_length=1, max_length=250)
    field_type: DepartureFieldType = "text"
    required: bool = False
    placeholder: str = Field(default="", max_length=250)
    options: list[str] = Field(default_factory=list, max_length=100)
    is_active: bool = True

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Treść pytania nie może być pusta")
        return stripped

    @field_validator("placeholder")
    @classmethod
    def strip_placeholder(cls, value: str) -> str:
        return value.strip()

    @field_validator("options")
    @classmethod
    def normalize_options(cls, value: list[str]) -> list[str]:
        return [option.strip() for option in value if option.strip()]

    @model_validator(mode="after")
    def validate_options(self):
        choice_type = self.field_type in {"select", "radio", "multiselect"}
        if choice_type and len(self.options) < 2:
            raise ValueError("Pole wyboru wymaga co najmniej dwóch opcji")
        if not choice_type and self.options:
            raise ValueError("Ten typ pola nie obsługuje opcji")
        if len(self.options) != len(set(self.options)):
            raise ValueError("Opcje nie mogą się powtarzać")
        return self


class DepartureFieldsUpdate(BaseModel):
    fields: list[DepartureFieldDraft] = Field(..., min_length=3, max_length=100)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [field.id for field in self.fields if field.id is not None]
        if len(ids) != len(set(ids)):
            raise ValueError("Pole ankiety może wystąpić tylko raz")
        return self


class DepartureFieldResponse(BaseModel):
    id: int
    key: str
    label: str
    field_type: DepartureFieldType
    required: bool
    placeholder: str
    options: list[str]
    position: int
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartureInterviewCreate(BaseModel):
    answers: dict[str, Any]

    @model_validator(mode="after")
    def limit_payload(self):
        if len(json.dumps(self.answers, ensure_ascii=False)) > 100_000:
            raise ValueError("Ankieta zawiera zbyt dużo danych")
        return self


class DepartureAnswerResponse(BaseModel):
    key: str
    label: str
    field_type: str
    value: Any = None


class DepartureVolunteerResponse(BaseModel):
    id: int
    full_name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class DepartureInterviewResponse(BaseModel):
    id: int
    volunteer_id: int
    departure_date: date
    departure_reason: str
    stay_in_contact: bool
    answers: list[DepartureAnswerResponse]
    completed_by_id: int | None
    created_at: datetime
    updated_at: datetime
    volunteer: DepartureVolunteerResponse

    model_config = ConfigDict(from_attributes=True)


class DepartureSelfServiceResponse(BaseModel):
    volunteer: DepartureVolunteerResponse
    fields: list[DepartureFieldResponse]
    interview: DepartureInterviewResponse | None
