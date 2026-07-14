"""Dependency injection for the departure interview workflow."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.recruitment.repositories.departures import DepartureRepository
from app.modules.recruitment.services.departures import DepartureService


def get_departure_repository(
    session: Session = Depends(get_db),
) -> DepartureRepository:
    return DepartureRepository(session)


def get_departure_service(
    repo: DepartureRepository = Depends(get_departure_repository),
) -> DepartureService:
    return DepartureService(repo)
