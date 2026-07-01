"""Load deterministic, non-production sample data into the public schema."""

from datetime import UTC, date, datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.core_data.models import User
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.function import Function, volunteer_function
from app.modules.pi.models.group import (
    BeneficiaryAssignment,
    Group,
    group_volunteer,
)
from app.modules.pi.models.volunteer import Volunteer
from app.modules.recruitment.constants import DEFAULT_FIELDS
from app.modules.recruitment.models import RecruitmentField, RecruitmentSubmission
from app.modules.security.services.password import hash_password

DEMO_PASSWORD = "DemoChangeMe123!"
SAMPLE_VOLUNTEER_COUNT = 10
SAMPLE_BENEFICIARY_COUNT = 10
SAMPLE_GROUP_COUNT = 4


def load_sample_data(session: Session) -> None:
    """Populate an empty schema with a complete, deterministic demo data set."""
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

    functions = [
        Function(name="Koordynator", is_system=True, is_active=True),
        Function(name="Wsparcie seniorów", is_system=False, is_active=True),
        Function(name="Logistyka", is_system=False, is_active=True),
    ]
    session.add_all(functions)
    session.flush()
    session.execute(
        volunteer_function.insert(),
        [
            {
                "volunteer_id": volunteer.id,
                "function_id": functions[index % len(functions)].id,
            }
            for index, volunteer in enumerate(volunteers)
        ],
    )

    group_names = [
        "Grupa Północ",
        "Grupa Południe",
        "Grupa Wschód",
        "Grupa Zachód",
    ]
    groups = [
        Group(name=name, leader_id=volunteers[index].id)
        for index, name in enumerate(group_names)
    ]
    session.add_all(groups)
    session.flush()
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
    session.add_all(
        [
            BeneficiaryAssignment(
                beneficiary_id=beneficiary.id,
                volunteer_id=volunteers[index].id,
                is_main=True,
                additional_info="Główny kontakt demonstracyjny.",
            )
            for index, beneficiary in enumerate(beneficiaries)
        ]
    )

    fields: list[RecruitmentField] = []
    for position, values in enumerate(DEFAULT_FIELDS):
        field = RecruitmentField(
            position=position,
            options=[],
            is_active=True,
            **values,
        )
        fields.append(field)
        session.add(field)
    session.flush()
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


def main() -> None:
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
                load_sample_data(session)
            except RuntimeError as error:
                raise SystemExit(str(error)) from error
    finally:
        engine.dispose()

    print(
        "public: sample data loaded "
        f"({SAMPLE_VOLUNTEER_COUNT} volunteers, "
        f"{SAMPLE_BENEFICIARY_COUNT} beneficiaries, {SAMPLE_GROUP_COUNT} groups)"
    )
    print("demo login: demo.admin@example.com / DemoChangeMe123!")


if __name__ == "__main__":
    main()
