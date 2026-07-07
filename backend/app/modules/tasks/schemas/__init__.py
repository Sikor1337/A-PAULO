"""Task schemas."""
from datetime import date, datetime

from pydantic import BaseModel, Field


class TaskCreateRequest(BaseModel):
    """New task with optional initial checklist and assignees."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    department_id: int
    event_id: int | None = None
    due_date: date | None = None
    assignee_ids: list[int] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)


class TaskUpdateRequest(BaseModel):
    """Partial task update; assignee_ids replaces the whole set when given."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = Field(None, max_length=20)
    department_id: int | None = None
    event_id: int | None = None
    clear_event: bool = False
    due_date: date | None = None
    clear_due_date: bool = False
    assignee_ids: list[int] | None = None


class ChecklistItemCreateRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=300)


class ChecklistItemUpdateRequest(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=300)
    is_done: bool | None = None


class ChecklistItemResponse(BaseModel):
    id: int
    label: str
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
