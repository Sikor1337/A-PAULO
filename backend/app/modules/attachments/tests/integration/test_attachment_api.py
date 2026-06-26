from collections.abc import Generator
from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.errors import register_error_handlers
from app.modules.attachments.api import router as attachments_router
from app.modules.attachments.dependencies import get_attachment_service
from app.modules.attachments.services import AttachmentService
from app.modules.attachments.storage import LocalAttachmentStorage
from app.modules.core_data.models import User
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
    function = FunctionService(db_session).create_function(name="Odwiedziny")
    volunteer = VolunteerService(db_session).create_volunteer(
        full_name="Anna Wolontariusz",
        email="anna.bo@example.com",
        join_date=datetime(2026, 1, 10, 9, 0),
        function_ids=[function.id],
    )
    group = GroupService(db_session).create_group(name="Grupa BO")
    beneficiary = BeneficiaryService(db_session).create_beneficiary(
        full_name="Jan BO",
        address="ul. Testowa 1",
        group_id=group["id"],
        bo_enrolled=True,
    )
    GroupService(db_session).update_group(
        group["id"],
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
            session=db_session,
            storage=LocalAttachmentStorage(tmp_path),
            max_size_bytes=10 * 1024,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_attachment_service] = override_service

    with TestClient(app) as client:
        upload_response = client.post(
            "/api/v1/attachments/bo-cards",
            params={
                "group_id": group["id"],
                "beneficiary_id": beneficiary.id,
                "volunteer_id": volunteer.id,
                "period": "2026-06",
                "filename": "karta.pdf",
            },
            content=b"%PDF-1.4",
            headers={"Content-Type": "application/pdf"},
        )
        assert upload_response.status_code == 200
        uploaded = upload_response.json()
        assert uploaded["display_name"] == "karta.pdf"
        assert uploaded["created_by_username"] == "admin"
        assert uploaded["size_bytes"] == 8

        list_response = client.get(
            "/api/v1/attachments/bo-cards",
            params={"group_id": group["id"]},
        )
        assert list_response.status_code == 200
        assert [item["id"] for item in list_response.json()] == [uploaded["id"]]

        overview_response = client.get(
            "/api/v1/attachments/bo-cards/all",
            params={"search": "Jan", "limit": 10},
        )
        assert overview_response.status_code == 200
        overview = overview_response.json()
        assert overview["total"] == 1
        assert overview["items"][0]["id"] == uploaded["id"]
        assert overview["items"][0]["group_name"] == "Grupa BO"
        assert overview["items"][0]["beneficiary_name"] == "Jan BO"
        assert overview["items"][0]["volunteer_name"] == "Anna Wolontariusz"

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
            "/api/v1/attachments/bo-cards/all",
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
            "/api/v1/attachments/bo-cards/all/download",
            params={"search": "Jan"},
        )
        assert archive_response.status_code == 200
        assert archive_response.headers["x-bo-cards-included"] == "1"
        with ZipFile(BytesIO(archive_response.content)) as archive:
            names = archive.namelist()
            assert len(names) == 1
            assert names[0].endswith("Karta czerwiec.pdf")
            assert archive.read(names[0]) == b"%PDF-1.4"

        delete_response = client.delete(f"/api/v1/attachments/{uploaded['id']}")
        assert delete_response.status_code == 200

        empty_list_response = client.get(
            "/api/v1/attachments/bo-cards",
            params={"group_id": group["id"]},
        )
        assert empty_list_response.status_code == 200
        assert empty_list_response.json() == []

    app.dependency_overrides.clear()
