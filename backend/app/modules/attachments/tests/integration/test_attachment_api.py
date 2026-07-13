from collections.abc import Generator
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import register_error_handlers
from app.infrastructure.storage import LocalAttachmentStorage
from app.modules.attachments.api import router as attachments_router
from app.modules.attachments.dependencies import get_attachment_service
from app.modules.attachments.repositories import AttachmentRepository
from app.modules.attachments.services import AttachmentService
from app.modules.audit.repositories import AuditRepository
from app.modules.audit.services import SqlAuditService
from app.modules.core_data.models import User
from app.modules.pi.repositories import (
    BeneficiaryAssignmentRepository,
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
from app.modules.security.dependencies import get_current_user


def test_bo_card_attachment_api_flow(
    db_session: Session,
    admin_user: User,
    tmp_path,
) -> None:
    audit = SqlAuditService(AuditRepository(db_session))
    function = FunctionService(FunctionRepository(db_session)).create_function(
        name="Odwiedziny"
    )
    volunteer = VolunteerService(
        VolunteerRepository(db_session), audit
    ).create_volunteer(
        actor=admin_user,
        request=VolunteerCreateRequest(
            full_name="Anna Wolontariusz",
            email="anna.bo@example.com",
            join_date=datetime(2026, 1, 10, 9, 0),
            function_ids=[function.id],
        ),
    )
    group_service = GroupService(GroupRepository(db_session), audit)
    group = group_service.create_group(name="Grupa BO", actor=admin_user)
    beneficiary = BeneficiaryService(
        BeneficiaryRepository(db_session), audit
    ).create_beneficiary(
        actor=admin_user,
        request=BeneficiaryCreateRequest(
            full_name="Jan BO",
            address="ul. Testowa 1",
            group_id=group["id"],
            bo_enrolled=True,
        ),
    )
    group_service.update_group(
        group["id"],
        actor=admin_user,
        assignments=[
            {
                "beneficiary": beneficiary.id,
                "volunteers": [{"id": volunteer.id, "additional_info": ""}],
                "main_volunteer": volunteer.id,
            }
        ],
    )

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(attachments_router, prefix="/api/v1")

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_service() -> AttachmentService:
        return AttachmentService(
            repo=AttachmentRepository(db_session),
            group_repo=GroupRepository(db_session),
            beneficiary_repo=BeneficiaryRepository(db_session),
            volunteer_repo=VolunteerRepository(db_session),
            assignment_repo=BeneficiaryAssignmentRepository(db_session),
            storage=LocalAttachmentStorage(tmp_path),
            max_size_bytes=10 * 1024,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_attachment_service] = override_service

    with TestClient(app) as client:
        upload_response = client.post(
            "/api/v1/attachments/bo-cards",
            data={
                "group_id": group["id"],
                "beneficiary_id": beneficiary.id,
                "volunteer_id": volunteer.id,
                "period": "2026-06",
            },
            files={"content": ("karta.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert upload_response.status_code == 201, upload_response.text
        uploaded = upload_response.json()
        assert uploaded["display_name"] == "karta.pdf"
        assert uploaded["created_by_username"] == "admin"
        assert uploaded["size_bytes"] == 8

        list_response = client.get(
            "/api/v1/attachments/bo-cards",
            params={"group_id": group["id"]},
        )
        assert list_response.status_code == 200
        listed = list_response.json()
        assert listed["total"] == 1
        assert [item["id"] for item in listed["items"]] == [uploaded["id"]]

        overview_response = client.get(
            "/api/v1/attachments/bo-cards",
            params={"search": "Jan", "limit": 10},
        )
        assert overview_response.status_code == 200
        overview = overview_response.json()
        assert overview["total"] == 1
        assert overview["items"][0]["id"] == uploaded["id"]
        assert overview["items"][0]["group_name"] == "Grupa BO"
        assert overview["items"][0]["beneficiary_name"] == "Jan BO"
        assert overview["items"][0]["volunteer_name"] == "Anna Wolontariusz"

        exact_period_response = client.get(
            "/api/v1/attachments/bo-cards",
            params={"period": "2026-06"},
        )
        assert exact_period_response.status_code == 200
        assert exact_period_response.json()["total"] == 1

        inverted_range_response = client.get(
            "/api/v1/attachments/bo-cards",
            params={"period_from": "2026-07", "period_to": "2026-06"},
        )
        assert inverted_range_response.status_code == 422

        legacy_all_response = client.get("/api/v1/attachments/bo-cards/all")
        assert legacy_all_response.status_code == 404

        patch_response = client.patch(
            f"/api/v1/attachments/{uploaded['id']}",
            json={
                "display_name": "Karta czerwiec.pdf",
                "description": "Sprawdzone przez koordynatora",
            },
        )
        assert patch_response.status_code == 200
        assert patch_response.json()["display_name"] == "Karta czerwiec.pdf"
        assert patch_response.json()["description"] == "Sprawdzone przez koordynatora"

        commented_response = client.get(
            "/api/v1/attachments/bo-cards",
            params={"has_comment": True},
        )
        assert commented_response.status_code == 200
        assert commented_response.json()["total"] == 1

        content_response = client.get(
            f"/api/v1/attachments/{uploaded['id']}/content",
        )
        assert content_response.status_code == 200
        assert content_response.content == b"%PDF-1.4"
        assert content_response.headers["content-type"] == "application/pdf"

        archive_response = client.get(
            "/api/v1/attachments/bo-cards/download",
            params={"search": "Jan"},
        )
        assert archive_response.status_code == 200
        assert archive_response.headers["x-bo-cards-included"] == "1"
        with ZipFile(BytesIO(archive_response.content)) as archive:
            names = archive.namelist()
            assert len(names) == 1
            assert names[0].endswith("Karta czerwiec.pdf")
            assert archive.read(names[0]) == b"%PDF-1.4"

        group_service.delete_group(group["id"], actor=admin_user)
        db_session.expire_all()
        retained_response = client.get(f"/api/v1/attachments/{uploaded['id']}")
        assert retained_response.status_code == 200
        assert retained_response.json()["group_id"] is None

        retained_content_response = client.get(
            f"/api/v1/attachments/{uploaded['id']}/content",
        )
        assert retained_content_response.status_code == 200
        assert retained_content_response.content == b"%PDF-1.4"

        delete_response = client.delete(f"/api/v1/attachments/{uploaded['id']}")
        assert delete_response.status_code == 200

        empty_list_response = client.get(
            "/api/v1/attachments/bo-cards",
            params={"group_id": group["id"]},
        )
        assert empty_list_response.status_code == 200
        assert empty_list_response.json()["items"] == []
        assert empty_list_response.json()["total"] == 0

        invalid_query_response = client.get(
            "/api/v1/attachments/bo-cards",
            params={"group_id": 0},
        )
        assert invalid_query_response.status_code == 422

        invalid_upload_response = client.post(
            "/api/v1/attachments/bo-cards",
            data={
                "group_id": group["id"],
                "beneficiary_id": beneficiary.id,
                "volunteer_id": volunteer.id,
                "period": "06-2026",
            },
            files={"content": ("karta.txt", b"text", "text/plain")},
        )
        assert invalid_upload_response.status_code == 422

    app.dependency_overrides.clear()
