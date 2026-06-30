"""Validation and response DTOs for calendar events."""

from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.calendar.models.constants import DEFAULT_TIMEZONE

EventStatus = Literal["draft", "published", "cancelled"]
EventVisibility = Literal["organization", "admins"]


def _normalize_rrule(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    rule = value.strip().upper()
    if rule.startswith("RRULE:"):
        rule = rule[6:]
    parts = dict(part.split("=", 1) for part in rule.split(";") if "=" in part)
    if parts.get("FREQ") not in {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}:
        raise ValueError("Reguła cykliczności musi zawierać obsługiwane FREQ")
    return rule


class EventBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10_000)
    starts_at: datetime
    ends_at: datetime
    timezone: str = Field(default=DEFAULT_TIMEZONE, max_length=64)
    is_all_day: bool = False
    location: str = Field(default="", max_length=300)
    recurrence_rule: str | None = Field(default=None, max_length=500)
    status: EventStatus = "published"
    visibility: EventVisibility = "organization"

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tytuł nie może być pusty")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Nieznana strefa czasowa") from exc
        return value

    @field_validator("recurrence_rule")
    @classmethod
    def validate_recurrence(cls, value: str | None) -> str | None:
        return _normalize_rrule(value)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.ends_at < self.starts_at:
            raise ValueError(
                "Data zakończenia nie może być wcześniejsza od rozpoczęcia"
            )
        return self


class EventCreateRequest(EventBase):
    pass


class EventUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str | None = Field(default=None, max_length=64)
    is_all_day: bool | None = None
    location: str | None = Field(default=None, max_length=300)
    recurrence_rule: str | None = Field(default=None, max_length=500)
    status: EventStatus | None = None
    visibility: EventVisibility | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Tytuł nie może być pusty")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Nieznana strefa czasowa") from exc
        return value

    @field_validator("recurrence_rule")
    @classmethod
    def validate_recurrence(cls, value: str | None) -> str | None:
        return _normalize_rrule(value)


class EventResponse(EventBase):
    id: int
    uid: str
    author_id: int
    author_name: str
    sequence: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
