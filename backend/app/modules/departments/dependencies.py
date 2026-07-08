"""Dependencies for the departments module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.departments.repositories.departments import DepartmentRepository
from app.modules.departments.services.departments import DepartmentService


def get_department_repository(
    session: Session = Depends(get_db),
) -> DepartmentRepository:
    return DepartmentRepository(session)


def get_department_service(
    repo: DepartmentRepository = Depends(get_department_repository),
) -> DepartmentService:
    """Get department service dependency."""
    return DepartmentService(repo)
