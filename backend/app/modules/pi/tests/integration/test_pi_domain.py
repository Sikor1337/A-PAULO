from collections.abc import Generator
from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import register_error_handlers
from app.modules.audit.repositories import AuditRepository
from app.modules.audit.services import SqlAuditService
from app.modules.pi.api.volunteers import router as volunteers_router
from app.modules.pi.repositories import (
    BeneficiaryRepository,
    FunctionRepository,
    GroupRepository,
    VolunteerRepository,
)
from app.modules.pi.schemas.beneficiaries import BeneficiaryCreateRequest
from app.modules.pi.schemas.volunteers import VolunteerCreateRequest
from app.modules.pi.services.beneficiaries import BeneficiaryService
from app.modules.pi.services.functions import FunctionService
from app.modules.pi.services.groups import GroupService
from app.modules.pi.services.volunteers import VolunteerService
from scripts.seed_required_data import seed_system_functions


def test_services_create_group_assignments_and_enriched_volunteer(
    db_session: Session,
) -> None:
    seed_system_functions(db_session)
    db_session.flush()
    audit = SqlAuditService(AuditRepository(db_session))
    actor = SimpleNamespace(id=999, email="system@example.com")
    function_service = FunctionService(FunctionRepository(db_session))
    volunteer_service = VolunteerService(VolunteerRepository(db_session), audit)
    beneficiary_service = BeneficiaryService(BeneficiaryRepository(db_session), audit)
    group_service = GroupService(GroupRepository(db_session), audit)

    function = function_service.create_function(name="Odwiedziny")
    volunteer = volunteer_service.create_volunteer(
        actor=actor,
        request=VolunteerCreateRequest(
            full_name="Anna Wolontariusz",
            email="anna.w@example.com",
            phone="+48 123 456 789",
            join_date=datetime(2026, 1, 10, 9, 0),
            function_ids=[function.id],
        ),
    )
    group = group_service.create_group(
        actor=actor,
        name="Grupa Północ",
        leader_id=volunteer.id,
    )
    beneficiary = beneficiary_service.create_beneficiary(
        actor=actor,
        request=BeneficiaryCreateRequest(
            full_name="Jan Podopieczny",
            address="ul. Testowa 1",
            group_id=group["id"],
            bo_enrolled=True,
        ),
    )

    detail = group_service.update_group(
        group["id"],
        actor=actor,
        assignments=[
            {
                "beneficiary": beneficiary.id,
                "volunteers": [
                    {"id": volunteer.id, "additional_info": "Kontakt we wtorki"}
                ],
                "main_volunteer": volunteer.id,
            }
        ],
    )

    assert detail["leader_name"] == "Anna Wolontariusz"
    assert detail["beneficiaries"] == [
        {
            "id": beneficiary.id,
            "full_name": "Jan Podopieczny",
            "volunteers": [
                {
                    "id": volunteer.id,
                    "full_name": "Anna Wolontariusz",
                    "is_main": True,
                    "additional_info": "Kontakt we wtorki",
                }
            ],
        }
    ]

    enriched_volunteer = volunteer_service.get_volunteer_by_id(volunteer.id)
    assert enriched_volunteer.manual_functions == ["Odwiedziny"]
    assert enriched_volunteer.derived_functions == [
        "Przewodnik",
        "Lider Podopiecznego",
    ]
    assert enriched_volunteer.functions == [
        "Odwiedziny",
        "Przewodnik",
        "Lider Podopiecznego",
    ]
    assert enriched_volunteer.led_group == "Grupa Północ"
    assert enriched_volunteer.assigned_groups == "Grupa Północ"
    assert enriched_volunteer.main_for_beneficiaries == ["Jan Podopieczny"]


def test_pi_api_exposes_resource_flow(api_client) -> None:
    function_response = api_client.post(
        "/api/v1/functions",
        json={"name": "Zakupy"},
    )
    assert function_response.status_code == 200
    function = function_response.json()

    volunteer_response = api_client.post(
        "/api/v1/volunteers",
        json={
            "full_name": "Piotr Wolontariusz",
            "email": "piotr@example.com",
            "phone": "+48 987 654 321",
            "join_date": "2026-02-01T10:00:00",
            "function_ids": [function["id"]],
        },
    )
    assert volunteer_response.status_code == 200
    volunteer = volunteer_response.json()
    assert volunteer["manual_functions"] == ["Zakupy"]

    beneficiary_response = api_client.post(
        "/api/v1/beneficiaries",
        json={
            "full_name": "Maria Podopieczna",
            "address": "ul. Dobra 2",
            "bo_enrolled": False,
        },
    )
    assert beneficiary_response.status_code == 200
    beneficiary = beneficiary_response.json()

    group_response = api_client.post(
        "/api/v1/groups",
        json={
            "name": "Grupa Centrum",
            "leader": volunteer["id"],
            "assignments": [
                {
                    "beneficiary": beneficiary["id"],
                    "volunteers": [
                        {
                            "id": volunteer["id"],
                            "additional_info": "Preferowany kontakt rano",
                        }
                    ],
                    "main_volunteer": volunteer["id"],
                }
            ],
        },
    )
    assert group_response.status_code == 200
    group = group_response.json()
    assert group["leader_name"] == "Piotr Wolontariusz"
    assert group["beneficiaries"][0]["volunteers"][0]["is_main"] is True

    assignments_response = api_client.get("/api/v1/assignments")
    assert assignments_response.status_code == 200
    assignment = assignments_response.json()[0]
    assert assignment["beneficiary_id"] == beneficiary["id"]
    assert assignment["volunteer_id"] == volunteer["id"]

    volunteer_detail_response = api_client.get(f"/api/v1/volunteers/{volunteer['id']}")
    assert volunteer_detail_response.status_code == 200
    volunteer_detail = volunteer_detail_response.json()
    assert volunteer_detail["assigned_groups"] == "Grupa Centrum"
    assert "Lider Podopiecznego" in volunteer_detail["derived_functions"]

    function_list_response = api_client.get(
        "/api/v1/functions",
        params={"name": "zak"},
    )
    assert function_list_response.status_code == 200
    assert [item["name"] for item in function_list_response.json()] == ["Zakupy"]


def test_pi_api_requires_authentication(db_session: Session) -> None:
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(volunteers_router, prefix="/api/v1")

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        response = client.get("/api/v1/volunteers")

    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid authorization header"


def test_function_only_volunteer_update_persists(api_client) -> None:
    """Regression (PAP-79 review): empty audit delta must not roll back writes."""
    function = api_client.post("/api/v1/functions", json={"name": "Transport"}).json()
    volunteer = api_client.post(
        "/api/v1/volunteers",
        json={
            "full_name": "Ola Testowa",
            "email": "ola.testowa@example.com",
            "join_date": "2026-03-01T09:00:00",
        },
    ).json()

    response = api_client.patch(
        f"/api/v1/volunteers/{volunteer['id']}",
        json={"function_ids": [function["id"]]},
    )
    assert response.status_code == 200
    assert response.json()["function_ids"] == [function["id"]]

    fetched = api_client.get(f"/api/v1/volunteers/{volunteer['id']}").json()
    assert fetched["function_ids"] == [function["id"]]


def test_history_only_beneficiary_update_persists(api_client) -> None:
    """Regression (PAP-79 review): history is part of the audit snapshot."""
    beneficiary = api_client.post(
        "/api/v1/beneficiaries",
        json={"full_name": "Jan Historyczny", "address": "ul. Prosta 1"},
    ).json()

    response = api_client.patch(
        f"/api/v1/beneficiaries/{beneficiary['id']}",
        json={"history": "Nowy wpis"},
    )
    assert response.status_code == 200

    fetched = api_client.get(f"/api/v1/beneficiaries/{beneficiary['id']}").json()
    assert fetched["history"] == "Nowy wpis"
