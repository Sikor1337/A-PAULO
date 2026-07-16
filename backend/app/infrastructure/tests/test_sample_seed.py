"""Regression tests for the deterministic public sample data."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.function import volunteer_function
from app.modules.pi.models.group import BeneficiaryAssignment, Group, group_volunteer
from app.modules.pi.models.volunteer import Volunteer
from app.modules.recruitment.models import (
    BeneficiaryRecruitmentField,
    DepartureField,
    RecruitmentField,
    RecruitmentOnboardingMeeting,
    RecruitmentSubmission,
)
from scripts.seed_required_data import (
    BENEFICIARY_RECRUITMENT_FIELDS,
    DEPARTURE_FIELDS,
    VOLUNTEER_RECRUITMENT_FIELDS,
)
from scripts.seed_sample_data import load_onboarding_scenarios, load_sample_data


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
    beneficiary_assignments = db_session.scalar(
        select(func.count()).select_from(BeneficiaryAssignment)
    )
    bo_beneficiary_assignments = db_session.scalar(
        select(func.count())
        .select_from(BeneficiaryAssignment)
        .join(Beneficiary, Beneficiary.id == BeneficiaryAssignment.beneficiary_id)
        .where(Beneficiary.bo_enrolled.is_(True))
    )
    function_assignments = db_session.scalar(
        select(func.count()).select_from(volunteer_function)
    )
    group_leaders = db_session.scalar(
        select(func.count()).select_from(Group).where(Group.leader_id.is_not(None))
    )
    volunteer_field_count = db_session.scalar(
        select(func.count()).select_from(RecruitmentField)
    )
    departure_field_count = db_session.scalar(
        select(func.count()).select_from(DepartureField)
    )
    beneficiary_field_count = db_session.scalar(
        select(func.count()).select_from(BeneficiaryRecruitmentField)
    )

    assert volunteer_count == 10
    assert beneficiary_count == 10
    assert group_count == 4
    assert grouped_volunteers == 10
    assert grouped_beneficiaries == 10
    assert beneficiary_assignments == 10
    assert bo_beneficiary_assignments == 5
    assert function_assignments == 0
    assert group_leaders == 4
    assert volunteer_field_count == len(VOLUNTEER_RECRUITMENT_FIELDS)
    assert departure_field_count == len(DEPARTURE_FIELDS)
    assert beneficiary_field_count == len(BENEFICIARY_RECRUITMENT_FIELDS)

    onboarding = db_session.scalars(
        select(RecruitmentSubmission).where(
            RecruitmentSubmission.status == "ONBOARDING"
        )
    ).all()
    progress = sorted(
        sum(
            meeting.attended_at is not None
            for meeting in submission.onboarding_meetings
        )
        for submission in onboarding
    )
    meeting_count = db_session.scalar(
        select(func.count()).select_from(RecruitmentOnboardingMeeting)
    )
    assert progress == [0, 2, 3, 4]
    assert meeting_count == 16

    assert load_onboarding_scenarios(db_session) == 0
    assert (
        db_session.scalar(select(func.count()).select_from(RecruitmentSubmission)) == 5
    )
