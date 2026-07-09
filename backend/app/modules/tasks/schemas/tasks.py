"""Task schemas."""
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.tasks.models.tasks import TaskStatus


class TaskCreateRequest(BaseModel):
    """New task with optional initial checklist and assignees."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    department_id: int = Field(ge=1)
    event_id: int | None = Field(None, ge=1)
    due_date: date | None = None
    assignee_ids: list[int] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @field_validator("checklist", mode="before")
    @classmethod
    def strip_labels(cls, value: list[str] | None) -> list[str] | None:
        """Trim checklist labels and drop blank ones."""
        if not isinstance(value, list):
            return value
        return [
            label.strip()
            for label in value
            if isinstance(label, str) and label.strip()
        ]


class TaskUpdateRequest(BaseModel):
    """Partial task update; assignee_ids replaces the whole set when given."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    department_id: int | None = Field(None, ge=1)
    event_id: int | None = Field(None, ge=1)
    clear_event: bool = False
    due_date: date | None = None
    clear_due_date: bool = False
    assignee_ids: list[int] | None = None

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def forbid_value_with_clear_flag(self) -> Self:
        """Reject contradictory input: a new value plus its clear_* flag."""
        if self.clear_event and self.event_id is not None:
            raise ValueError("Nie można jednocześnie ustawić i wyczyścić wydarzenia")
        if self.clear_due_date and self.due_date is not None:
            raise ValueError("Nie można jednocześnie ustawić i wyczyścić terminu")
        return self


class ChecklistItemCreateRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=300)
    volunteer_id: int | None = Field(None, ge=1)

    @field_validator("label", mode="before")
    @classmethod
    def strip_label(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class ChecklistItemUpdateRequest(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=300)
    is_done: bool | None = None
    volunteer_id: int | None = Field(None, ge=1)
    clear_volunteer: bool = False

    @field_validator("label", mode="before")
    @classmethod
    def strip_label(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def forbid_value_with_clear_flag(self) -> Self:
        """Reject contradictory input: a new value plus its clear_* flag."""
        if self.clear_volunteer and self.volunteer_id is not None:
            raise ValueError(
                "Nie można jednocześnie przypisać i wyczyścić wolontariusza"
            )
        return self


class ChecklistItemResponse(BaseModel):
    id: int
    label: str
    volunteer_id: int | None
    volunteer_name: str | None
    is_done: bool
    done_at: datetime | None
    position: int


class TaskAssigneeResponse(BaseModel):
    volunteer_id: int
    full_name: str


class TaskResponse(BaseModel):
    """Task with progress, checklist and assignees."""

    id: int
    title: str
    description: str
    status: str
    department_id: int
    department_name: str | None
    event_id: int | None
    event_title: str | None
    due_date: date | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    checklist: list[ChecklistItemResponse]
    assignees: list[TaskAssigneeResponse]
    checklist_done: int
    checklist_total: int
