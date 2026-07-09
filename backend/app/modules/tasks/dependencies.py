"""Dependencies for the tasks module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.tasks.repositories import TaskRepository
from app.modules.tasks.services import TaskService


def get_task_repository(session: Session = Depends(get_db)) -> TaskRepository:
    return TaskRepository(session)


def get_task_service(
    repo: TaskRepository = Depends(get_task_repository),
) -> TaskService:
    """Get task service dependency."""
    return TaskService(repo)
