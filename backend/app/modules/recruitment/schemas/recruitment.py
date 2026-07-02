"""Request and response schemas for recruitment."""

import json
import re
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.errors import ValidationException
from app.modules.recruitment.constants import (
    ALLOWED_FIELD_TYPES,
    ANSWER_MAX_LENGTHS,
    CHOICE_FIELD_TYPES,
    MAX_ANSWERS_JSON_SIZE,
    MAX_LONG_ANSWER_LENGTH,
    MAX_SHORT_ANSWER_LENGTH,
    MULTIPLE_CHOICE_FIELD_TYPES,
    SINGLE_CHOICE_FIELD_TYPES,
)
from app.modules.recruitment.models import RecruitmentField

FieldType = Literal[
    "text",
    "textarea",
    "email",
    "tel",
    "date",
    "select",
    "radio",
    "multiselect",
    "checkbox",
]


class RecruitmentFieldDraft(BaseModel):
    """One field in the form draft saved atomically by the editor."""

    id: int | None = Field(default=None, ge=1)
    label: str = Field(..., min_length=1, max_length=250)
    field_type: FieldType = "text"
    required: bool = False
    placeholder: str = Field(default="", max_length=250)
    options: list[str] = Field(default_factory=list, max_length=100)
    is_active: bool = True

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        label = value.strip()
        if not label:
            raise ValueError("Treść pytania nie może być pusta")
        return label

    @field_validator("placeholder")
    @classmethod
    def strip_placeholder(cls, value: str) -> str:
        return value.strip()

    @field_validator("options")
    @classmethod
    def normalize_options(cls, options: list[str]) -> list[str]:
        return [option.strip() for option in options if option.strip()]

    @model_validator(mode="after")
    def validate_options(self):
        if self.field_type not in ALLOWED_FIELD_TYPES:
            raise ValueError("Nieobsługiwany typ pola")
        if self.field_type in CHOICE_FIELD_TYPES and len(self.options) < 2:
            raise ValueError("Pole wyboru wymaga co najmniej dwóch opcji")
        if self.field_type not in CHOICE_FIELD_TYPES and self.options:
            raise ValueError("Ten typ pola nie obsługuje listy opcji")
        if len(self.options) != len(set(self.options)):
            raise ValueError("Opcje odpowiedzi nie mogą się powtarzać")
        return self


class RecruitmentFormUpdateRequest(BaseModel):
    fields: list[RecruitmentFieldDraft] = Field(..., min_length=3, max_length=200)

    @model_validator(mode="after")
    def validate_unique_ids(self):
        ids = [field.id for field in self.fields if field.id is not None]
        if len(ids) != len(set(ids)):
            raise ValueError("Każde pole może wystąpić w formularzu tylko raz")
        return self


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
    applicant_name: str
    applicant_email: str
    initial_answers: dict[str, Any] = Field(default_factory=dict)
    submission_status: str | None = None
    return_reason: str | None = None


class RecruitmentSubmissionCreate(BaseModel):
    answers: dict[str, Any]

    @model_validator(mode="after")
    def validate_payload_size(self):
        if len(json.dumps(self.answers, ensure_ascii=False)) > MAX_ANSWERS_JSON_SIZE:
            raise ValueError("Formularz zawiera zbyt dużo danych")
        return self

    def validated_answers(self, fields: list[RecruitmentField]) -> list[dict[str, Any]]:
        """Validate answers against the current form definition."""

        result: list[dict[str, Any]] = []
        for field in fields:
            value = self.answers.get(field.key)
            if field.field_type == "checkbox":
                if value is not None and not isinstance(value, bool):
                    self._invalid_answer(field.label)
            elif field.field_type in MULTIPLE_CHOICE_FIELD_TYPES:
                if value is not None and (
                    not isinstance(value, list)
                    or any(not isinstance(item, str) for item in value)
                ):
                    self._invalid_answer(field.label)
                if isinstance(value, list):
                    value = [item.strip() for item in value if item.strip()]
            elif value is not None and not isinstance(value, str):
                raise ValidationException(f"Pole „{field.label}” musi zawierać tekst")

            if isinstance(value, str):
                value = value.strip()
            empty = value is None or value == "" or value == [] or value is False
            if field.required and empty:
                raise ValidationException(f"Pole „{field.label}” jest wymagane")

            if (
                not empty
                and field.field_type in SINGLE_CHOICE_FIELD_TYPES
                and value not in field.options
            ):
                self._invalid_answer(field.label)
            if (
                not empty
                and field.field_type in MULTIPLE_CHOICE_FIELD_TYPES
                and (
                    len(value) != len(set(value))
                    or any(item not in field.options for item in value)
                )
            ):
                self._invalid_answer(field.label)
            if (
                not empty
                and field.field_type == "email"
                and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(value))
            ):
                raise ValidationException("Podaj prawidłowy adres e-mail")

            max_length = ANSWER_MAX_LENGTHS.get(
                field.key,
                MAX_LONG_ANSWER_LENGTH
                if field.field_type == "textarea"
                else MAX_SHORT_ANSWER_LENGTH,
            )
            if isinstance(value, str) and len(value) > max_length:
                raise ValidationException(
                    f"Odpowiedź w polu „{field.label}” jest zbyt długa"
                )
            if isinstance(value, list) and any(
                len(item) > MAX_SHORT_ANSWER_LENGTH for item in value
            ):
                self._invalid_answer(field.label)
            if not empty and field.field_type == "date":
                try:
                    date.fromisoformat(str(value))
                except ValueError as error:
                    raise ValidationException(
                        f"Nieprawidłowa data w polu „{field.label}”"
                    ) from error

            result.append(
                {
                    "key": field.key,
                    "label": field.label,
                    "field_type": field.field_type,
                    "value": value,
                }
            )
        return result

    @staticmethod
    def _invalid_answer(label: str) -> None:
        raise ValidationException(f"Nieprawidłowa odpowiedź w polu „{label}”")


class RecruitmentAnswerResponse(BaseModel):
    key: str
    label: str
    field_type: str
    value: Any = None


class RecruitmentOnboardingMeetingResponse(BaseModel):
    meeting_type: str
    attended_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class RecruitmentSubmissionResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    phone: str
    social_link: str
    availability: str
    answers: list[RecruitmentAnswerResponse]
    status: str
    return_reason: str | None
    decision_comment: str | None
    volunteer_id: int | None
    onboarding_meetings: list[RecruitmentOnboardingMeetingResponse] = Field(
        default_factory=list
    )
    submitted_at: datetime
    status_changed_at: datetime
    created_at: datetime
    updated_at: datetime

    @field_validator("answers", mode="before")
    @classmethod
    def normalize_legacy_answers(cls, value: Any) -> list[dict[str, Any]]:
        """Keep historical object-shaped answers from breaking the whole list."""

        if value is None:
            return []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return []
        if isinstance(value, dict):
            return [
                {
                    "key": str(key),
                    "label": str(key).replace("_", " ").strip().capitalize(),
                    "field_type": (
                        "checkbox"
                        if isinstance(answer, bool)
                        else "multiselect"
                        if isinstance(answer, list)
                        else "text"
                    ),
                    "value": answer,
                }
                for key, answer in value.items()
            ]
        return value

    model_config = ConfigDict(from_attributes=True)


class ReturnSubmissionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class DecisionRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class OnboardingAttendanceRequest(BaseModel):
    attended: bool
