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
from app.modules.recruitment.models import RecruitmentField, RecruitmentSubmission
from app.modules.recruitment.models.constants import DEFAULT_FIELDS
from app.modules.security.services.password import hash_password

DEMO_PASSWORD = "DemoChangeMe123!"


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

    with Session(engine) as session:
        if session.query(User).first():
            raise SystemExit("public already contains users; refusing duplicate seed")

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
        volunteers = [
            Volunteer(
                full_name="Jan Wolontariusz",
                email="jan.wolontariusz@example.com",
                phone="+48 500 100 200",
                social_link="https://example.com/jan",
                status="Aktywny",
                join_date=datetime(2025, 3, 15),
                notes="Przykładowy lider grupy.",
                history="Dołączył w ramach danych demonstracyjnych.",
            ),
            Volunteer(
                full_name="Maria Wolontariuszka",
                email="maria.wolontariuszka@example.com",
                phone="+48 500 300 400",
                status="Aktywny",
                join_date=datetime(2025, 9, 1),
                notes="Dane demonstracyjne.",
                history="",
            ),
        ]
        session.add_all([admin, candidate, *volunteers])
        session.flush()

        functions = [
            Function(name="Koordynator", is_system=True, is_active=True),
            Function(name="Wsparcie seniorów", is_system=False, is_active=True),
        ]
        session.add_all(functions)
        session.flush()
        session.execute(
            volunteer_function.insert(),
            [
                {"volunteer_id": volunteers[0].id, "function_id": functions[0].id},
                {"volunteer_id": volunteers[1].id, "function_id": functions[1].id},
            ],
        )

        group = Group(name="Grupa demonstracyjna", leader_id=volunteers[0].id)
        session.add(group)
        session.flush()
        session.execute(
            group_volunteer.insert(),
            [
                {"group_id": group.id, "volunteer_id": volunteer.id}
                for volunteer in volunteers
            ],
        )

        beneficiaries = [
            Beneficiary(
                full_name="Zofia Przykładowa",
                address="ul. Przykładowa 1, Warszawa",
                phone="+48 600 100 100",
                family_phone="+48 600 200 200",
                description="Przykładowa podopieczna.",
                group_id=group.id,
                status="OBECNY",
                bo_enrolled=True,
                last_priest_visit=date(2026, 5, 10),
                last_volunteer_meeting=date(2026, 6, 15),
                history="Rekord demonstracyjny.",
            ),
            Beneficiary(
                full_name="Piotr Testowy",
                address="ul. Testowa 2, Warszawa",
                description="Drugi rekord demonstracyjny.",
                group_id=group.id,
                status="OBECNY",
                bo_enrolled=False,
                history="",
            ),
        ]
        session.add_all(beneficiaries)
        session.flush()
        session.add_all(
            [
                BeneficiaryAssignment(
                    beneficiary_id=beneficiaries[0].id,
                    volunteer_id=volunteers[0].id,
                    is_main=True,
                    additional_info="Główny kontakt demonstracyjny.",
                ),
                BeneficiaryAssignment(
                    beneficiary_id=beneficiaries[1].id,
                    volunteer_id=volunteers[1].id,
                    is_main=True,
                    additional_info="Przykładowe przypisanie.",
                ),
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

    engine.dispose()
    print("public: sample data loaded")
    print("demo login: demo.admin@example.com / DemoChangeMe123!")


if __name__ == "__main__":
    main()
