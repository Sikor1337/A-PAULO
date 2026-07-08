"""Task repository."""

from sqlalchemy.orm import Session, selectinload

from app.infrastructure.sql.repository import SQLRepository
from app.modules.calendar.models import CalendarEvent
from app.modules.departments.models import Department
from app.modules.pi.models.volunteer import Volunteer
from app.modules.tasks.models import Task, TaskAssignee, TaskChecklistItem


class TaskRepository(SQLRepository):
    """Data access for tasks, checklist items and assignees."""

    def __init__(self, session: Session):
        self.session = session

    def _query(self):
        return self.session.query(Task).options(
            selectinload(Task.checklist), selectinload(Task.assignees)
        )

    def get_by_id(self, task_id: int) -> Task | None:
        return self._query().filter(Task.id == task_id).first()

    def list_all(
        self,
        department_id: int | None = None,
        event_id: int | None = None,
        status: str | None = None,
        volunteer_id: int | None = None,
    ) -> list[Task]:
        query = self._query()
        if department_id is not None:
            query = query.filter(Task.department_id == department_id)
        if event_id is not None:
            query = query.filter(Task.event_id == event_id)
        if status:
            query = query.filter(Task.status == status)
        if volunteer_id is not None:
            query = query.join(TaskAssignee).filter(
                TaskAssignee.volunteer_id == volunteer_id
            )
        return query.order_by(Task.created_at.desc()).all()

    def create(self, **kwargs) -> Task:
        task = Task(**kwargs)
        self.session.add(task)
        return task

    def update(self, task: Task, **kwargs) -> Task:
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return task

    def delete(self, task: Task) -> None:
        self.session.delete(task)

    def add_checklist_item(
        self,
        task_id: int,
        label: str,
        position: int,
        volunteer_id: int | None = None,
    ) -> TaskChecklistItem:
        item = TaskChecklistItem(
            task_id=task_id,
            label=label,
            position=position,
            volunteer_id=volunteer_id,
        )
        self.session.add(item)
        return item

    def get_checklist_item(
        self, task_id: int, item_id: int
    ) -> TaskChecklistItem | None:
        return (
            self.session.query(TaskChecklistItem)
            .filter(
                TaskChecklistItem.id == item_id,
                TaskChecklistItem.task_id == task_id,
            )
            .first()
        )

    def delete_checklist_item(self, item: TaskChecklistItem) -> None:
        self.session.delete(item)

    def replace_assignees(self, task: Task, volunteer_ids: list[int]) -> None:
        unique_ids = list(dict.fromkeys(volunteer_ids))
        task.assignees = [
            TaskAssignee(task_id=task.id, volunteer_id=volunteer_id)
            for volunteer_id in unique_ids
        ]

    def department_exists(self, department_id: int) -> bool:
        return (
            self.session.query(Department.id)
            .filter(Department.id == department_id)
            .first()
            is not None
        )

    def event_exists(self, event_id: int) -> bool:
        return (
            self.session.query(CalendarEvent.id)
            .filter(CalendarEvent.id == event_id)
            .first()
            is not None
        )

    def existing_volunteer_ids(self, volunteer_ids: list[int]) -> set[int]:
        if not volunteer_ids:
            return set()
        rows = (
            self.session.query(Volunteer.id)
            .filter(Volunteer.id.in_(volunteer_ids))
            .all()
        )
        return {row[0] for row in rows}

    def department_names(self, department_ids: set[int]) -> dict[int, str]:
        if not department_ids:
            return {}
        rows = (
            self.session.query(Department.id, Department.name)
            .filter(Department.id.in_(department_ids))
            .all()
        )
        return dict(rows)

    def event_titles(self, event_ids: set[int]) -> dict[int, str]:
        if not event_ids:
            return {}
        rows = (
            self.session.query(CalendarEvent.id, CalendarEvent.title)
            .filter(CalendarEvent.id.in_(event_ids))
            .all()
        )
        return dict(rows)

    def volunteer_names(self, volunteer_ids: list[int]) -> dict[int, str]:
        if not volunteer_ids:
            return {}
        rows = (
            self.session.query(Volunteer.id, Volunteer.full_name)
            .filter(Volunteer.id.in_(volunteer_ids))
            .all()
        )
        return dict(rows)
