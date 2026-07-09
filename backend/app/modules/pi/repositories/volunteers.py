"""Volunteer repository for PI domain."""

from sqlalchemy import delete, func, insert
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.function import Function, volunteer_function
from app.modules.pi.models.group import BeneficiaryAssignment, Group
from app.modules.pi.models.volunteer import Volunteer


class VolunteerRepository(SQLRepository):
    """Repository for Volunteer model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, volunteer_id: int) -> Volunteer | None:
        """Get volunteer by ID."""
        return (
            self.session.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
        )

    def get_by_email(self, email: str) -> Volunteer | None:
        """Get volunteer by email."""
        return self.session.query(Volunteer).filter(Volunteer.email == email).first()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        full_name: str | None = None,
        email: str | None = None,
        status: str | None = None,
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
        self,
        full_name: str | None = None,
        email: str | None = None,
        status: str | None = None,
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
        return volunteer

    def delete(self, volunteer: Volunteer) -> None:
        """Delete volunteer."""
        self.session.delete(volunteer)

    def exists(self, email: str) -> bool:
        """Check if volunteer with email exists."""
        return self.get_by_email(email) is not None

    def list_emails(self) -> list[str]:
        """List all volunteer emails (for bulk-import duplicate checks)."""
        return [row[0] for row in self.session.query(Volunteer.email).all()]

    def enrich(self, volunteer: Volunteer) -> Volunteer:
        """Populate volunteer projection fields used by API responses."""
        manual_functions = (
            self.session.query(Function)
            .join(volunteer_function, Function.id == volunteer_function.c.function_id)
            .filter(
                volunteer_function.c.volunteer_id == volunteer.id,
                Function.is_active.is_(True),
            )
            .order_by(Function.name)
            .all()
        )
        volunteer.function_ids = [item.id for item in manual_functions]
        volunteer.manual_functions = [item.name for item in manual_functions]
        led_group = (
            self.session.query(Group.name)
            .filter(Group.leader_id == volunteer.id)
            .first()
        )
        volunteer.led_group = led_group[0] if led_group else None
        assigned_groups = (
            self.session.query(Group.name)
            .join(Beneficiary, Beneficiary.group_id == Group.id)
            .join(
                BeneficiaryAssignment,
                BeneficiaryAssignment.beneficiary_id == Beneficiary.id,
            )
            .filter(BeneficiaryAssignment.volunteer_id == volunteer.id)
            .distinct()
            .order_by(Group.name)
            .all()
        )
        volunteer.assigned_groups = ", ".join(row[0] for row in assigned_groups)
        main_rows = (
            self.session.query(Beneficiary.full_name)
            .join(BeneficiaryAssignment)
            .filter(
                BeneficiaryAssignment.volunteer_id == volunteer.id,
                BeneficiaryAssignment.is_main.is_(True),
            )
            .all()
        )
        volunteer.main_for_beneficiaries = [row[0] for row in main_rows]
        derived = []
        if volunteer.led_group:
            derived.append("Przewodnik")
        if volunteer.main_for_beneficiaries:
            derived.append("Lider Podopiecznego")
        volunteer.derived_functions = derived
        volunteer.functions = list(
            dict.fromkeys([*volunteer.manual_functions, *derived])
        )
        return volunteer

    def replace_functions(self, volunteer_id: int, function_ids: list[int]) -> None:
        unique_ids = list(dict.fromkeys(function_ids or []))
        if unique_ids:
            count = (
                self.session.query(Function.id)
                .filter(Function.id.in_(unique_ids), Function.is_active.is_(True))
                .count()
            )
            if count != len(unique_ids):
                raise ValueError("missing_function")
        self.session.execute(
            delete(volunteer_function).where(
                volunteer_function.c.volunteer_id == volunteer_id
            )
        )
        if unique_ids:
            self.session.execute(
                insert(volunteer_function),
                [
                    {"volunteer_id": volunteer_id, "function_id": function_id}
                    for function_id in unique_ids
                ],
            )
