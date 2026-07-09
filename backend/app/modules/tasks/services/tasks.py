"""Task business logic.

Status rules:
- a manual status change (PATCH status) marks the task as manually managed;
  the checklist automation never overrides a manual decision,
- on automatically managed tasks, checking the last checklist item completes
  the task and un-checking an item reopens it (W_TRAKCIE),
- ZROBIONE always stamps completed_at; leaving it clears the stamp.
"""

from datetime import UTC, datetime
from typing import Any

from app.core.errors import NotFoundError
from app.modules.tasks.models.tasks import Task, TaskStatus
from app.modules.tasks.repositories.tasks import TaskRepository
from app.modules.tasks.schemas.tasks import (
    ChecklistItemCreateRequest,
    ChecklistItemResponse,
    ChecklistItemUpdateRequest,
    TaskAssigneeResponse,
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)


class TaskService:
    """Tasks with checklists, assignees and progress tracking."""

    def __init__(self, repo: TaskRepository):
        self.repo = repo

    def get_task(self, task_id: int) -> Task:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Zadanie nie istnieje")
        return task

    def get_task_detail(self, task_id: int) -> TaskResponse:
        return self._to_responses([self.get_task(task_id)])[0]

    def list_tasks(
        self,
        department_id: int | None = None,
        event_id: int | None = None,
        status: TaskStatus | None = None,
        volunteer_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TaskResponse]:
        tasks = self.repo.list_all(
            department_id=department_id,
            event_id=event_id,
            status=status.value if status else None,
            volunteer_id=volunteer_id,
            skip=skip,
            limit=limit,
        )
        return self._to_responses(tasks)

    def create_task(self, request: TaskCreateRequest) -> TaskResponse:
        try:
            self._validate_refs(
                request.department_id, request.event_id, request.assignee_ids
            )
            task = self.repo.create(
                title=request.title,
                description=request.description,
                department_id=request.department_id,
                event_id=request.event_id,
                due_date=request.due_date,
            )
            self.repo.flush()
            for position, label in enumerate(request.checklist):
                self.repo.add_checklist_item(task.id, label, position)
            if request.assignee_ids:
                self.repo.replace_assignees(task, request.assignee_ids)
            self.repo.flush()
            self.repo.refresh(task)
            self.repo.commit(skip_audit=True)
            return self._to_responses([task])[0]
        except Exception:
            self.repo.rollback()
            raise

    def update_task(self, task_id: int, request: TaskUpdateRequest) -> TaskResponse:
        try:
            task = self.get_task(task_id)
            self._validate_refs(
                request.department_id, request.event_id, request.assignee_ids or []
            )
            updates: dict[str, Any] = {}
            if request.title is not None:
                updates["title"] = request.title
            if request.description is not None:
                updates["description"] = request.description
            if request.department_id is not None:
                updates["department_id"] = request.department_id
            if request.event_id is not None:
                updates["event_id"] = request.event_id
            if request.due_date is not None:
                updates["due_date"] = request.due_date
            if request.status is not None:
                updates["status"] = request.status.value
            if request.clear_event:
                updates["event_id"] = None
            if request.clear_due_date:
                updates["due_date"] = None

            task = self.repo.update(task, **updates)
            if request.status is not None:
                # A human decision: the checklist automation backs off from now on.
                task.status_is_manual = True
                task.completed_at = (
                    datetime.now(UTC) if request.status is TaskStatus.ZROBIONE else None
                )
            if request.assignee_ids is not None:
                self.repo.replace_assignees(task, request.assignee_ids)
            self.repo.flush()
            self.repo.refresh(task)
            self.repo.commit(skip_audit=True)
            return self._to_responses([task])[0]
        except Exception:
            self.repo.rollback()
            raise

    def delete_task(self, task_id: int) -> None:
        try:
            task = self.get_task(task_id)
            self.repo.delete(task)
            self.repo.commit(skip_audit=True)
        except Exception:
            self.repo.rollback()
            raise

    def add_checklist_item(
        self, task_id: int, request: ChecklistItemCreateRequest
    ) -> TaskResponse:
        try:
            task = self.get_task(task_id)
            self._ensure_volunteer_exists(request.volunteer_id)
            position = (
                max((item.position for item in task.checklist), default=-1) + 1
            )
            self.repo.add_checklist_item(
                task.id, request.label, position, request.volunteer_id
            )
            self.repo.flush()
            self.repo.refresh(task)
            self._reconcile_status(task)
            self.repo.flush()
            self.repo.commit(skip_audit=True)
            return self._to_responses([task])[0]
        except Exception:
            self.repo.rollback()
            raise

    def update_checklist_item(
        self, task_id: int, item_id: int, request: ChecklistItemUpdateRequest
    ) -> TaskResponse:
        try:
            task = self.get_task(task_id)
            item = self.repo.get_checklist_item(task_id, item_id)
            if not item:
                raise NotFoundError("Punkt checklisty nie istnieje")
            if request.label is not None:
                item.label = request.label
            if request.volunteer_id is not None:
                self._ensure_volunteer_exists(request.volunteer_id)
                item.volunteer_id = request.volunteer_id
            if request.clear_volunteer:
                item.volunteer_id = None
            if request.is_done is not None:
                item.is_done = request.is_done
                item.done_at = datetime.now(UTC) if item.is_done else None
            self.repo.flush()
            self.repo.refresh(task)
            self._reconcile_status(task)
            self.repo.flush()
            self.repo.commit(skip_audit=True)
            return self._to_responses([task])[0]
        except Exception:
            self.repo.rollback()
            raise

    def delete_checklist_item(self, task_id: int, item_id: int) -> TaskResponse:
        try:
            task = self.get_task(task_id)
            item = self.repo.get_checklist_item(task_id, item_id)
            if not item:
                raise NotFoundError("Punkt checklisty nie istnieje")
            self.repo.delete_checklist_item(item)
            self.repo.flush()
            self.repo.refresh(task)
            self._reconcile_status(task)
            self.repo.flush()
            self.repo.commit(skip_audit=True)
            return self._to_responses([task])[0]
        except Exception:
            self.repo.rollback()
            raise

    def _reconcile_status(self, task: Task) -> None:
        """Auto-complete/reopen from the checklist, unless a human decided."""
        if task.status_is_manual or not task.checklist:
            return
        all_done = all(item.is_done for item in task.checklist)
        if all_done and task.status != TaskStatus.ZROBIONE.value:
            task.status = TaskStatus.ZROBIONE.value
            task.completed_at = datetime.now(UTC)
        elif not all_done and task.status == TaskStatus.ZROBIONE.value:
            task.status = TaskStatus.W_TRAKCIE.value
            task.completed_at = None

    def _ensure_volunteer_exists(self, volunteer_id: int | None) -> None:
        if volunteer_id is not None and not self.repo.existing_volunteer_ids(
            [volunteer_id]
        ):
            raise NotFoundError("Wolontariusz nie istnieje")

    def _validate_refs(
        self,
        department_id: int | None,
        event_id: int | None,
        assignee_ids: list[int],
    ) -> None:
        """Business validation: all referenced records must exist."""
        if department_id is not None and not self.repo.department_exists(
            department_id
        ):
            raise NotFoundError("Dział nie istnieje")
        if event_id is not None and not self.repo.event_exists(event_id):
            raise NotFoundError("Wydarzenie nie istnieje")
        if assignee_ids:
            existing = self.repo.existing_volunteer_ids(assignee_ids)
            missing = [vid for vid in assignee_ids if vid not in existing]
            if missing:
                raise NotFoundError(f"Nie istnieją wolontariusze: {missing}")

    def _to_responses(self, tasks: list[Task]) -> list[TaskResponse]:
        """Build response schemas with names resolved in bulk queries."""
        department_names = self.repo.department_names(
            {task.department_id for task in tasks}
        )
        event_titles = self.repo.event_titles(
            {task.event_id for task in tasks if task.event_id is not None}
        )
        assignee_ids = {
            assignee.volunteer_id for task in tasks for assignee in task.assignees
        }
        item_owner_ids = {
            item.volunteer_id
            for task in tasks
            for item in task.checklist
            if item.volunteer_id is not None
        }
        volunteer_names = self.repo.volunteer_names(
            list(assignee_ids | item_owner_ids)
        )
        return [
            self._to_response(task, department_names, event_titles, volunteer_names)
            for task in tasks
        ]

    def _to_response(
        self,
        task: Task,
        department_names: dict[int, str],
        event_titles: dict[int, str],
        volunteer_names: dict[int, str],
    ) -> TaskResponse:
        checklist = [
            ChecklistItemResponse(
                id=item.id,
                label=item.label,
                volunteer_id=item.volunteer_id,
                volunteer_name=(
                    volunteer_names.get(item.volunteer_id)
                    if item.volunteer_id is not None
                    else None
                ),
                is_done=item.is_done,
                done_at=item.done_at,
                position=item.position,
            )
            for item in task.checklist
        ]
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            department_id=task.department_id,
            department_name=department_names.get(task.department_id),
            event_id=task.event_id,
            event_title=(
                event_titles.get(task.event_id) if task.event_id else None
            ),
            due_date=task.due_date,
            completed_at=task.completed_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
            checklist=checklist,
            assignees=[
                TaskAssigneeResponse(
                    volunteer_id=assignee.volunteer_id,
                    full_name=volunteer_names.get(assignee.volunteer_id, ""),
                )
                for assignee in task.assignees
            ],
            checklist_done=sum(1 for item in task.checklist if item.is_done),
            checklist_total=len(task.checklist),
        )
