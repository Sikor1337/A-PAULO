"""Volunteer repository for PI domain."""

from sqlalchemy import delete, func, insert
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.function import (
    Function,
    SystemFunctionKey,
    volunteer_function,
)
from app.modules.pi.models.group import BeneficiaryAssignment, Group
from app.modules.pi.models.volunteer import Volunteer
from app.modules.pi.schemas.volunteers import (
    VolunteerCreateRequest,
    VolunteerUpdateRequest,
)


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

    def create(self, request: VolunteerCreateRequest) -> Volunteer:
        """Create new volunteer."""
        volunteer = Volunteer(
            full_name=request.full_name,
            email=str(request.email),
            phone=request.phone,
            social_link=request.social_link,
            status=request.status,
            join_date=request.join_date,
            notes=request.notes,
            history=request.history,
        )
        self.session.add(volunteer)
        return volunteer

    def update(
        self, volunteer: Volunteer, request: VolunteerUpdateRequest
    ) -> Volunteer:
        """Update volunteer."""
        fields = request.model_fields_set
        if "full_name" in fields and request.full_name is not None:
            volunteer.full_name = request.full_name
        if "email" in fields and request.email is not None:
            volunteer.email = str(request.email)
        if "phone" in fields:
            volunteer.phone = request.phone
        if "social_link" in fields:
            volunteer.social_link = request.social_link
        if "status" in fields and request.status is not None:
            volunteer.status = request.status
        if "join_date" in fields and request.join_date is not None:
            volunteer.join_date = request.join_date
        if "notes" in fields and request.notes is not None:
            volunteer.notes = request.notes
        if "history" in fields and request.history is not None:
            volunteer.history = request.history
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

    def _system_function_names(
        self, keys: list[SystemFunctionKey]
    ) -> dict[SystemFunctionKey, str]:
        """Resolve display names from seeded SQL reference data."""
        if not keys:
            return {}
        rows = (
            self.session.query(Function.system_key, Function.name)
            .filter(Function.system_key.in_([key.value for key in keys]))
            .all()
        )
        names = {SystemFunctionKey(key): name for key, name in rows if key is not None}
        missing = set(keys) - set(names)
        if missing:
            missing_keys = ", ".join(sorted(key.value for key in missing))
            raise RuntimeError(
                "Missing required system functions in SQL. "
                f"Run the required-data seed; missing: {missing_keys}"
            )
        return names

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
        derived_keys: list[SystemFunctionKey] = []
        if volunteer.led_group:
            derived_keys.append(SystemFunctionKey.GROUP_GUIDE)
        if volunteer.main_for_beneficiaries:
            derived_keys.append(SystemFunctionKey.BENEFICIARY_LEADER)
        system_function_names = self._system_function_names(derived_keys)
        derived = [system_function_names[key] for key in derived_keys]
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
