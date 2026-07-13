"""Load deterministic, non-production sample data into the public schema."""

import argparse
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.audit import AuditEntry
from app.core.config import get_settings
from app.modules.core_data.models import User
from app.modules.core_data.repositories.users import UserRepository
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.group import Group, group_volunteer
from app.modules.pi.models.volunteer import Volunteer
from app.modules.recruitment.constants import ONBOARDING_MEETING_TYPES
from app.modules.recruitment.models import (
    RecruitmentField,
    RecruitmentOnboardingMeeting,
    RecruitmentSubmission,
)
from app.modules.recruitment.repositories import RecruitmentRepository
from app.modules.recruitment.services import RecruitmentService
from app.modules.security.repositories import PermissionRepository
from app.modules.security.services.password import hash_password
from app.modules.security.services.permissions import PermissionService
from scripts.seed_required_data import PI_GROUPS, load_required_data

DEMO_PASSWORD = "DemoChangeMe123!"
SAMPLE_VOLUNTEER_COUNT = 10
SAMPLE_BENEFICIARY_COUNT = 10
SAMPLE_GROUP_COUNT = 4
SAMPLE_ONBOARDING_COUNT = 4


class NoOpAudit:
    """Skip audit records for non-production sample data."""

    def record(self, entry: AuditEntry) -> None:
        pass


def load_sample_data(session: Session) -> None:
    """Populate an empty schema with a complete, deterministic demo data set."""
    load_required_data(session)
    if session.query(User).first():
        raise RuntimeError("public already contains users; refusing duplicate seed")

    admin = User(
        username="demo.admin",
        email="demo.admin@example.com",
        first_name="Demo",
        last_name="Administrator",
        hashed_password=hash_password(DEMO_PASSWORD),
        status="admin",
        is_active=True,
    )
    candidate = User(
        username="demo.candidate",
        email="demo.candidate@example.com",
        first_name="Anna",
        last_name="Kandydatka",
        hashed_password=hash_password(DEMO_PASSWORD),
        status="new_volunteer",
        is_active=True,
    )
    volunteer_names = [
        "Jan Wolontariusz",
        "Maria Wolontariuszka",
        "Piotr Pomocny",
        "Anna Zaangażowana",
        "Tomasz Wspierający",
        "Katarzyna Aktywna",
        "Michał Serdeczny",
        "Joanna Pomocna",
        "Paweł Wolontariusz",
        "Ewa Wspierająca",
    ]
    volunteers = [
        Volunteer(
            full_name=name,
            email=f"demo.volunteer{index:02d}@example.com",
            phone=f"+48 500 100 {index:03d}",
            social_link=f"https://example.com/volunteer-{index}",
            status="Aktywny",
            join_date=datetime(2025, (index % 12) + 1, min(index + 5, 28)),
            notes=f"Wolontariusz demonstracyjny nr {index}.",
            history="Rekord utworzony przez seed danych przykładowych.",
        )
        for index, name in enumerate(volunteer_names, start=1)
    ]
    session.add_all([admin, candidate, *volunteers])
    session.flush()
    perm_repo = PermissionRepository(session)
    users_repo = UserRepository(session)
    audit = NoOpAudit()
    PermissionService(perm_repo, users_repo, audit).assign_default_group(admin)

    group_keys = [definition["system_key"] for definition in PI_GROUPS]
    groups = (
        session.query(Group)
        .filter(Group.system_key.in_(group_keys))
        .order_by(Group.system_key)
        .all()
    )
    session.execute(
        group_volunteer.insert(),
        [
            {
                "group_id": groups[index % len(groups)].id,
                "volunteer_id": volunteer.id,
            }
            for index, volunteer in enumerate(volunteers)
        ],
    )

    beneficiary_names = [
        "Zofia Przykładowa",
        "Piotr Testowy",
        "Helena Nowak",
        "Stanisław Kowalski",
        "Krystyna Wiśniewska",
        "Andrzej Wójcik",
        "Barbara Kamińska",
        "Józef Lewandowski",
        "Teresa Zielińska",
        "Henryk Szymański",
    ]
    beneficiaries = [
        Beneficiary(
            full_name=name,
            address=f"ul. Przykładowa {index}, Warszawa",
            phone=f"+48 600 100 {index:03d}",
            family_phone=f"+48 600 200 {index:03d}",
            description=f"Podopieczny demonstracyjny nr {index}.",
            group_id=groups[(index - 1) % len(groups)].id,
            status="OBECNY",
            bo_enrolled=index % 2 == 0,
            last_priest_visit=date(2026, 5, min(index + 5, 28)),
            last_volunteer_meeting=date(2026, 6, min(index + 10, 28)),
            history="Rekord utworzony przez seed danych przykładowych.",
        )
        for index, name in enumerate(beneficiary_names, start=1)
    ]
    session.add_all(beneficiaries)
    session.flush()

    fields = session.query(RecruitmentField).order_by(RecruitmentField.position).all()
    answer_values = {
        "full_name": "Anna Kandydatka",
        "email": candidate.email,
        "phone": "+48 700 100 100",
        "social_link": "https://example.com/anna",
        "availability": "Wtorki i czwartki",
    }
    now = datetime.now(UTC)
    session.add(
        RecruitmentSubmission(
            user_id=candidate.id,
            full_name="Anna Kandydatka",
            email=candidate.email,
            phone=answer_values["phone"],
            social_link=answer_values["social_link"],
            availability=answer_values["availability"],
            answers=[
                {
                    "key": field.key,
                    "label": field.label,
                    "field_type": field.field_type,
                    "value": answer_values.get(field.key),
                }
                for field in fields
            ],
            status="SUBMITTED",
            submitted_at=now,
            status_changed_at=now,
        )
    )
    session.commit()
    load_onboarding_scenarios(session)


def load_onboarding_scenarios(session: Session) -> int:
    """Add stable candidates with 0/4, 2/4, 3/4 and 4/4 progress."""

    load_required_data(session)
    audit = NoOpAudit()
    perm_repo = PermissionRepository(session)
    users_repo = UserRepository(session)
    perm_service = PermissionService(perm_repo, users_repo, audit)
    recruitment_repo = RecruitmentRepository(session)
    recruitment_service = RecruitmentService(recruitment_repo, perm_service, audit)
    fields = recruitment_service.list_fields()
    now = datetime.now(UTC)
    scenarios = [
        ("demo.onboarding0", "Karol Start", 0),
        ("demo.onboarding2", "Beata W Połowie", 2),
        ("demo.onboarding3", "Celina Prawie Gotowa", 3),
        ("demo.onboarding4", "Daniel Gotowy", 4),
    ]
    created = 0

    for index, (username, full_name, completed) in enumerate(scenarios, start=1):
        user = session.query(User).filter(User.username == username).one_or_none()
        if user is None:
            user = User(
                username=username,
                email=f"{username}@example.com",
                first_name=full_name.split()[0],
                last_name=" ".join(full_name.split()[1:]),
                hashed_password=hash_password(DEMO_PASSWORD),
                status="new_volunteer",
                is_active=True,
            )
            session.add(user)
            session.flush()

        submission = (
            session.query(RecruitmentSubmission)
            .filter(RecruitmentSubmission.user_id == user.id)
            .one_or_none()
        )
        if submission is not None:
            continue

        phone = f"+48 700 200 10{index}"
        values = {
            "full_name": full_name,
            "email": user.email,
            "phone": phone,
            "social_link": f"https://example.com/{username}",
            "availability": "Wieczory w tygodniu",
        }
        submission = RecruitmentSubmission(
            user_id=user.id,
            full_name=full_name,
            email=user.email,
            phone=phone,
            social_link=values["social_link"],
            availability=values["availability"],
            answers=[
                {
                    "key": field.key,
                    "label": field.label,
                    "field_type": field.field_type,
                    "value": values.get(field.key),
                }
                for field in fields
            ],
            status="ONBOARDING",
            submitted_at=now - timedelta(days=10 - index),
            status_changed_at=now - timedelta(days=5 - index),
        )
        session.add(submission)
        session.flush()
        session.add_all(
            [
                RecruitmentOnboardingMeeting(
                    submission_id=submission.id,
                    meeting_type=meeting_type,
                    attended_at=(
                        now - timedelta(days=completed - meeting_index)
                        if meeting_index < completed
                        else None
                    ),
                )
                for meeting_index, meeting_type in enumerate(ONBOARDING_MEETING_TYPES)
            ]
        )
        created += 1

    session.commit()
    return created


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recruitment-only",
        action="store_true",
        help="Add missing onboarding demo scenarios without resetting other data",
    )
    args = parser.parse_args()
    settings = get_settings()
    if settings.database_schema != "public":
        raise SystemExit("Sample data may only be loaded into the public schema")

    engine = create_engine(settings.database_url, pool_pre_ping=True)

    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute('SET search_path TO "public"')
        cursor.close()

    try:
        with Session(engine) as session:
            try:
                if args.recruitment_only:
                    created = load_onboarding_scenarios(session)
                else:
                    load_sample_data(session)
                    created = SAMPLE_ONBOARDING_COUNT
            except RuntimeError as error:
                raise SystemExit(str(error)) from error
    finally:
        engine.dispose()

    if args.recruitment_only:
        print("public: missing onboarding demo scenarios added")
    else:
        print(
            "public: sample data loaded "
            f"({SAMPLE_VOLUNTEER_COUNT} volunteers, "
            f"{SAMPLE_BENEFICIARY_COUNT} beneficiaries, "
            f"{SAMPLE_GROUP_COUNT} groups)"
        )
        print("demo login: demo.admin@example.com / DemoChangeMe123!")
    print(
        "onboarding demo logins: demo.onboarding0@example.com .. "
        "demo.onboarding4@example.com / DemoChangeMe123! "
        f"({created} added)"
    )


if __name__ == "__main__":
    main()
