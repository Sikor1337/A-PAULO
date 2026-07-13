"""Regression tests for the production reference-data seed (PAP-98)."""

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.departments.models import Department
from app.modules.pi.models import Function, Group
from app.modules.recruitment.models import (
    BeneficiaryRecruitmentField,
    DepartureField,
    RecruitmentField,
)
from app.modules.security.models import Permission, UserGroup
from scripts.seed_required_data import (
    BENEFICIARY_RECRUITMENT_FIELDS,
    DEPARTMENTS,
    DEPARTURE_FIELDS,
    PERMISSIONS,
    PI_GROUPS,
    SYSTEM_FUNCTIONS,
    VOLUNTEER_RECRUITMENT_FIELDS,
    load_required_data,
)


def _count(session: Session, model: type) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_required_seed_loads_every_catalog_and_is_idempotent(
    db_session: Session,
) -> None:
    first = load_required_data(db_session)
    db_session.commit()

    assert _count(db_session, Permission) == len(PERMISSIONS)
    assert _count(db_session, UserGroup) == 2
    assert _count(db_session, Function) == len(SYSTEM_FUNCTIONS)
    assert _count(db_session, Group) == len(PI_GROUPS)
    assert _count(db_session, Department) == len(DEPARTMENTS)
    assert _count(db_session, RecruitmentField) == len(VOLUNTEER_RECRUITMENT_FIELDS)
    assert _count(db_session, DepartureField) == len(DEPARTURE_FIELDS)
    assert _count(db_session, BeneficiaryRecruitmentField) == len(
        BENEFICIARY_RECRUITMENT_FIELDS
    )

    admin = db_session.scalar(select(UserGroup).where(UserGroup.system_key == "admin"))
    staff = db_session.scalar(select(UserGroup).where(UserGroup.system_key == "staff"))
    assert admin is not None
    assert staff is not None
    assert {item.code for item in admin.permissions} == {
        code for code, _, _, _ in PERMISSIONS
    }
    assert {item.code for item in staff.permissions} == {
        code for code, _, _, staff_default in PERMISSIONS if staff_default
    }
    assert sum(first.created.values()) > 0

    second = load_required_data(db_session)
    db_session.commit()

    assert second.created == {}
    assert second.updated == {}


def test_repeated_seed_preserves_supported_configuration_changes(
    db_session: Session,
) -> None:
    load_required_data(db_session)
    db_session.commit()

    department = db_session.scalar(
        select(Department).where(Department.system_key == "MEDIA")
    )
    group = db_session.scalar(select(Group).where(Group.system_key == "GROUP_A"))
    staff = db_session.scalar(select(UserGroup).where(UserGroup.system_key == "staff"))
    assert department is not None
    assert group is not None
    assert staff is not None
    department.name = "Komunikacja"
    department.is_archived = True
    group.name = "Grupa Północna"
    removed_code = next(iter(permission.code for permission in staff.permissions))
    staff.permissions = [
        permission
        for permission in staff.permissions
        if permission.code != removed_code
    ]
    db_session.commit()

    load_required_data(db_session)
    db_session.commit()

    assert department.name == "Komunikacja"
    assert department.is_archived is True
    assert group.name == "Grupa Północna"
    assert removed_code not in {permission.code for permission in staff.permissions}
    assert _count(db_session, Department) == len(DEPARTMENTS)
    assert _count(db_session, Group) == len(PI_GROUPS)


def test_seed_repairs_protected_fields_without_restoring_optional_questions(
    db_session: Session,
) -> None:
    load_required_data(db_session)
    db_session.commit()

    required = db_session.scalar(
        select(RecruitmentField).where(RecruitmentField.key == "full_name")
    )
    optional = db_session.scalar(
        select(RecruitmentField).where(RecruitmentField.key == "availability")
    )
    assert required is not None
    assert optional is not None
    db_session.delete(required)
    db_session.delete(optional)
    db_session.commit()

    load_required_data(db_session)
    db_session.commit()

    keys = set(db_session.scalars(select(RecruitmentField.key)).all())
    assert "full_name" in keys
    assert "availability" not in keys


def test_single_production_migration_contains_schema_only() -> None:
    versions_dir = Path(__file__).resolve().parents[3] / "alembic" / "versions"
    migrations = list(versions_dir.glob("*.py"))

    assert len(migrations) == 1
    source = migrations[0].read_text(encoding="utf-8")
    assert "bulk_insert" not in source
    assert "INSERT INTO" not in source.upper()
