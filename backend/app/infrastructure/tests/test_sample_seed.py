"""Regression tests for the deterministic public sample data."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.group import (
    BeneficiaryAssignment,
    Group,
    group_volunteer,
)
from app.modules.pi.models.volunteer import Volunteer
from scripts.seed_sample_data import load_sample_data


def test_sample_seed_restores_expected_people_and_group_assignments(
    db_session: Session,
) -> None:
    load_sample_data(db_session)

    volunteer_count = db_session.scalar(select(func.count()).select_from(Volunteer))
    beneficiary_count = db_session.scalar(select(func.count()).select_from(Beneficiary))
    group_count = db_session.scalar(select(func.count()).select_from(Group))
    grouped_volunteers = db_session.scalar(
        select(func.count()).select_from(group_volunteer)
    )
    grouped_beneficiaries = db_session.scalar(
        select(func.count())
        .select_from(Beneficiary)
        .where(Beneficiary.group_id.is_not(None))
    )
    main_assignments = db_session.scalar(
        select(func.count())
        .select_from(BeneficiaryAssignment)
        .where(BeneficiaryAssignment.is_main.is_(True))
    )

    assert volunteer_count == 10
    assert beneficiary_count == 10
    assert group_count == 4
    assert grouped_volunteers == 10
    assert grouped_beneficiaries == 10
    assert main_assignments == 10
