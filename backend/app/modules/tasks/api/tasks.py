"""Tasks API endpoints."""

from fastapi import APIRouter, Depends, Query

from app.modules.core_data.models import User
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_TASKS,
    CAN_VIEW_TASKS,
)
from app.modules.tasks.dependencies import get_task_service
from app.modules.tasks.models.tasks import TaskStatus
from app.modules.tasks.schemas.tasks import (
    ChecklistItemCreateRequest,
    ChecklistItemUpdateRequest,
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)
from app.modules.tasks.services.tasks import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    department_id: int | None = Query(None),
    event_id: int | None = Query(None),
    status: TaskStatus | None = Query(None),
    volunteer_id: int | None = Query(None),
    service: TaskService = Depends(get_task_service),
    _user: User = Depends(require_permission(CAN_VIEW_TASKS)),
):
    """List tasks with optional filters."""
    return service.list_tasks(
        department_id=department_id,
        event_id=event_id,
        status=status,
        volunteer_id=volunteer_id,
    )


@router.post("", response_model=TaskResponse)
def create_task(
    request: TaskCreateRequest,
    service: TaskService = Depends(get_task_service),
    _user: User = Depends(require_permission(CAN_MANAGE_TASKS)),
):
    """Create a task with optional initial checklist and assignees."""
    return service.create_task(request)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    _user: User = Depends(require_permission(CAN_VIEW_TASKS)),
):
    """Get one task."""
    return service.get_task_detail(task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    request: TaskUpdateRequest,
    service: TaskService = Depends(get_task_service),
    _user: User = Depends(require_permission(CAN_MANAGE_TASKS)),
):
    """Update a task; assignee_ids replaces the whole assignee set."""
    return service.update_task(task_id, request)


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    _user: User = Depends(require_permission(CAN_MANAGE_TASKS)),
):
    """Delete a task."""
    service.delete_task(task_id)
    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/checklist", response_model=TaskResponse)
def add_checklist_item(
    task_id: int,
    request: ChecklistItemCreateRequest,
    service: TaskService = Depends(get_task_service),
    _user: User = Depends(require_permission(CAN_MANAGE_TASKS)),
):
    """Add a checklist item, optionally owned by a volunteer."""
    return service.add_checklist_item(task_id, request)


@router.patch("/{task_id}/checklist/{item_id}", response_model=TaskResponse)
def update_checklist_item(
    task_id: int,
    item_id: int,
    request: ChecklistItemUpdateRequest,
    service: TaskService = Depends(get_task_service),
    _user: User = Depends(require_permission(CAN_MANAGE_TASKS)),
):
    """Tick/untick or rename a checklist item."""
    return service.update_checklist_item(task_id, item_id, request)


@router.delete("/{task_id}/checklist/{item_id}", response_model=TaskResponse)
def delete_checklist_item(
    task_id: int,
    item_id: int,
    service: TaskService = Depends(get_task_service),
    _user: User = Depends(require_permission(CAN_MANAGE_TASKS)),
):
    """Remove a checklist item."""
    return service.delete_checklist_item(task_id, item_id)
