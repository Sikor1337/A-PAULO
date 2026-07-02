"""Dependency injection for the departure interview workflow."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.recruitment.services.departures import DepartureService


def get_departure_service(session: Session = Depends(get_db)) -> DepartureService:
    return DepartureService(session)
