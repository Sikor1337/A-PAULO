"""Volunteer repository for PI domain."""
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.modules.pi.models.volunteer import Volunteer


class VolunteerRepository:
    """Repository for Volunteer model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, volunteer_id: int) -> Volunteer | None:
        """Get volunteer by ID."""
        return self.session.query(Volunteer).filter(Volunteer.id == volunteer_id).first()

    def get_by_email(self, email: str) -> Volunteer | None:
        """Get volunteer by email."""
        return self.session.query(Volunteer).filter(Volunteer.email == email).first()

    def list_all(
        self, skip: int = 0, limit: int = 100, full_name: str = None, email: str = None, status: str = None
    ) -> list[Volunteer]:
        """List volunteers with optional filters."""
        query = self.session.query(Volunteer)

        if full_name:
            query = query.filter(Volunteer.full_name.ilike(f"%{full_name}%"))
        if email:
            query = query.filter(Volunteer.email.ilike(f"%{email}%"))
        if status:
            query = query.filter(Volunteer.status == status)

        return query.order_by(Volunteer.full_name).offset(skip).limit(limit).all()

    def count(
        self, full_name: str = None, email: str = None, status: str = None
    ) -> int:
        """Count volunteers with optional filters."""
        query = self.session.query(func.count(Volunteer.id))

        if full_name:
            query = query.filter(Volunteer.full_name.ilike(f"%{full_name}%"))
        if email:
            query = query.filter(Volunteer.email.ilike(f"%{email}%"))
        if status:
            query = query.filter(Volunteer.status == status)

        return query.scalar() or 0

    def create(self, **kwargs) -> Volunteer:
        """Create new volunteer."""
        volunteer = Volunteer(**kwargs)
        self.session.add(volunteer)
        return volunteer

    def update(self, volunteer: Volunteer, **kwargs) -> Volunteer:
        """Update volunteer."""
        for key, value in kwargs.items():
            if hasattr(volunteer, key):
                setattr(volunteer, key, value)
        self.session.commit()
        self.session.refresh(volunteer)
        return volunteer

    def delete(self, volunteer: Volunteer) -> None:
        """Delete volunteer."""
        self.session.delete(volunteer)
        self.session.commit()

    def exists(self, email: str) -> bool:
        """Check if volunteer with email exists."""
        return self.get_by_email(email) is not None
