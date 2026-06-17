"""Volunteer service for PI domain."""
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.core.errors import NotFoundError, ConflictError
from app.modules.pi.models.volunteer import Volunteer
from app.modules.pi.models.group import Group, BeneficiaryAssignment
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.repositories.volunteers import VolunteerRepository


class VolunteerService:
    """Service for volunteer operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = VolunteerRepository(session)

    def _enrich_volunteer(self, volunteer: Volunteer) -> Volunteer:
        """Enrich volunteer with computed fields from database."""
        # led_group: name of group where volunteer is leader
        led_group = self.session.query(Group.name).filter(Group.leader_id == volunteer.id).first()
        volunteer.led_group = led_group[0] if led_group else None

        # assigned_groups: count of unique beneficiaries in assignments
        assigned_groups_count = self.session.query(
            func.count(func.distinct(BeneficiaryAssignment.beneficiary_id))
        ).filter(BeneficiaryAssignment.volunteer_id == volunteer.id).scalar()
        volunteer.assigned_groups = assigned_groups_count or 0

        # main_for_beneficiaries: list of beneficiary names where is_main=True
        main_beneficiaries = self.session.query(Beneficiary.full_name).join(
            BeneficiaryAssignment
        ).filter(
            BeneficiaryAssignment.volunteer_id == volunteer.id,
            BeneficiaryAssignment.is_main == True
        ).all()
        volunteer.main_for_beneficiaries = [b[0] for b in main_beneficiaries] if main_beneficiaries else []

        return volunteer

    def get_volunteer_by_id(self, volunteer_id: int) -> Volunteer:
        """Get volunteer by ID or raise NotFoundError."""
        volunteer = self.repo.get_by_id(volunteer_id)
        if not volunteer:
            raise NotFoundError(f"Volunteer with ID {volunteer_id} not found")
        return self._enrich_volunteer(volunteer)

    def list_volunteers(
        self, skip: int = 0, limit: int = 100, full_name: str = None, email: str = None, status: str = None
    ):
        """List volunteers with pagination and filters."""
        volunteers = self.repo.list_all(
            skip=skip, limit=limit, full_name=full_name, email=email, status=status
        )
        count = self.repo.count(full_name=full_name, email=email, status=status)
        
        # Enrich each volunteer with computed fields
        volunteers = [self._enrich_volunteer(v) for v in volunteers]
        return volunteers, count

    def create_volunteer(self, **kwargs) -> Volunteer:
        """Create new volunteer."""
        try:
            # Check if email already exists
            if self.repo.exists(kwargs.get("email")):
                raise ConflictError(f"Volunteer with email '{kwargs.get('email')}' already exists")

            volunteer = self.repo.create(**kwargs)
            self.session.flush()
            self.session.refresh(volunteer)
            self.session.commit()
            return self._enrich_volunteer(volunteer)
        except Exception:
            self.session.rollback()
            raise

    def update_volunteer(self, volunteer_id: int, **kwargs) -> Volunteer:
        """Update volunteer."""
        try:
            volunteer = self.get_volunteer_by_id(volunteer_id)

            # If email is being updated, check uniqueness (excluding current volunteer)
            if "email" in kwargs and kwargs["email"] != volunteer.email:
                if self.repo.exists(kwargs["email"]):
                    raise ConflictError(f"Volunteer with email '{kwargs['email']}' already exists")

            volunteer = self.repo.update(volunteer, **kwargs)
            self.session.flush()
            self.session.refresh(volunteer)
            self.session.commit()
            return self._enrich_volunteer(volunteer)
        except Exception:
            self.session.rollback()
            raise

    def delete_volunteer(self, volunteer_id: int) -> None:
        """Delete volunteer."""
        try:
            volunteer = self.get_volunteer_by_id(volunteer_id)
            self.repo.delete(volunteer)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
