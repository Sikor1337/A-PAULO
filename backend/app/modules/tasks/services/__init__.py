"""Task business logic.

Status rules:
- manually setting ZROBIONE stamps completed_at; leaving it clears the stamp,
- checking the last checklist item auto-completes the task,
- un-checking an item on a completed task reopens it (W_TRAKCIE).
"""

from datetime import UTC, datetime

from app.core.errors import NotFoundError, ValidationException
from app.modules.tasks.models import TASK_STATUSES, Task
from app.modules.tasks.repositories import TaskRepository


class TaskService:
    """Tasks with checklists, assignees and progress tracking."""

    def __init__(self, repo: TaskRepository):
        self.repo = repo

    def get_task(self, task_id: int) -> Task:
        task = self.repo.get_by_id(task_id)
        if not task:
            raise NotFoundError("Zadanie nie istnieje")
        return task

    def get_task_detail(self, task_id: int) -> dict:
        return self._serialize(self.get_task(task_id))

    def list_tasks(
        self,
        department_id: int | None = None,
        event_id: int | None = None,
        status: str | None = None,
        volunteer_id: int | None = None,
    ) -> list[dict]:
        if status and status not in TASK_STATUSES:
            raise ValidationException(
                f"Status musi być jednym z: {', '.join(TASK_STATUSES)}"
            )
        tasks = self.repo.list_all(
            department_id=department_id,
            event_id=event_id,
            status=status,
            volunteer_id=volunteer_id,
        )
        return [self._serialize(task) for task in tasks]

    def create_task(
        self,
        *,
        title: str,
        description: str = "",
        department_id: int,
        event_id: int | None = None,
        due_date=None,
        assignee_ids: list[int] | None = None,
        checklist: list[str] | None = None,
    ) -> dict:
        try:
            self._validate_refs(department_id, event_id, assignee_ids or [])
            task = self.repo.create(
                title=title.strip(),
                description=description.strip(),
                department_id=department_id,
                event_id=event_id,
                due_date=due_date,
            )
            self.repo.flush()
            for position, label in enumerate(checklist or []):
                label = label.strip()
                if label:
                    self.repo.add_checklist_item(task.id, label, position)
            if assignee_ids:
                self.repo.replace_assignees(task, assignee_ids)
            self.repo.flush()
            self.repo.refresh(task)
            self.repo.commit(skip_audit=True)
            return self._serialize(task)
        except Exception:
            self.repo.rollback()
            raise

    def update_task(self, task_id: int, **kwargs) -> dict:
        try:
            task = self.get_task(task_id)
            assignee_ids = kwargs.pop("assignee_ids", None)
            clear_event = kwargs.pop("clear_event", False)
            clear_due_date = kwargs.pop("clear_due_date", False)
            new_status = kwargs.get("status")
            if new_status and new_status not in TASK_STATUSES:
                raise ValidationException(
                    f"Status musi być jednym z: {', '.join(TASK_STATUSES)}"
                )
            self._validate_refs(
                kwargs.get("department_id"),
                kwargs.get("event_id"),
                assignee_ids or [],
            )
            if clear_event:
                kwargs["event_id"] = None
            if clear_due_date:
                kwargs["due_date"] = None

            task = self.repo.update(task, **kwargs)
            if new_status:
                task.completed_at = (
                    datetime.now(UTC) if new_status == "ZROBIONE" else None
                )
            if assignee_ids is not None:
                self.repo.replace_assignees(task, assignee_ids)
            self.repo.flush()
            self.repo.refresh(task)
            self.repo.commit(skip_audit=True)
            return self._serialize(task)
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

    def add_checklist_item(self, task_id: int, label: str) -> dict:
        try:
            task = self.get_task(task_id)
            position = (
                max((item.position for item in task.checklist), default=-1) + 1
            )
            self.repo.add_checklist_item(task.id, label.strip(), position)
            self._reconcile_status(task)
            self.repo.flush()
            self.repo.refresh(task)
            self.repo.commit(skip_audit=True)
            return self._serialize(task)
        except Exception:
            self.repo.rollback()
            raise

    def update_checklist_item(self, task_id: int, item_id: int, **kwargs) -> dict:
        try:
            task = self.get_task(task_id)
            item = self.repo.get_checklist_item(task_id, item_id)
            if not item:
                raise NotFoundError("Punkt checklisty nie istnieje")
            if "label" in kwargs and kwargs["label"] is not None:
                item.label = kwargs["label"].strip()
            if "is_done" in kwargs and kwargs["is_done"] is not None:
                item.is_done = kwargs["is_done"]
                item.done_at = datetime.now(UTC) if item.is_done else None
            self.repo.flush()
            self.repo.refresh(task)
            self._reconcile_status(task)
            self.repo.flush()
            self.repo.refresh(task)
            self.repo.commit(skip_audit=True)
            return self._serialize(task)
        except Exception:
            self.repo.rollback()
            raise

    def delete_checklist_item(self, task_id: int, item_id: int) -> dict:
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
            return self._serialize(task)
        except Exception:
            self.repo.rollback()
            raise

    def _reconcile_status(self, task: Task) -> None:
        """Auto-complete when the whole checklist is ticked; reopen otherwise."""
        if not task.checklist:
            return
        all_done = all(item.is_done for item in task.checklist)
        if all_done and task.status != "ZROBIONE":
            task.status = "ZROBIONE"
            task.completed_at = datetime.now(UTC)
        elif not all_done and task.status == "ZROBIONE":
            task.status = "W_TRAKCIE"
            task.completed_at = None

    def _validate_refs(
        self,
        department_id: int | None,
        event_id: int | None,
        assignee_ids: list[int],
    ) -> None:
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

    def _serialize(self, task: Task) -> dict:
        volunteer_ids = [assignee.volunteer_id for assignee in task.assignees]
        names = self.repo.volunteer_names(volunteer_ids)
        checklist = [
            {
                "id": item.id,
                "label": item.label,
                "is_done": item.is_done,
                "done_at": item.done_at,
                "position": item.position,
            }
            for item in task.checklist
        ]
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "department_id": task.department_id,
            "department_name": self.repo.department_name(task.department_id),
            "event_id": task.event_id,
            "event_title": (
                self.repo.event_title(task.event_id) if task.event_id else None
            ),
            "due_date": task.due_date,
            "completed_at": task.completed_at,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "checklist": checklist,
            "assignees": [
                {"volunteer_id": vid, "full_name": names.get(vid, "")}
                for vid in volunteer_ids
            ],
            "checklist_done": sum(1 for item in task.checklist if item.is_done),
            "checklist_total": len(task.checklist),
        }
