"""Integration tests for the bug reports module (PAP-83)."""

import io
import zipfile
from pathlib import Path

import pytest

from app.core.dependencies import get_attachment_storage
from app.core.errors import NotFoundError
from app.infrastructure.storage.attachments import StoredFile
from app.modules.core_data.models import User
from app.modules.security.dependencies import get_current_user
from app.modules.security.models import Permission, UserGroup, security_user_groups
from app.modules.security.models.constants import CAN_SUBMIT_BUG_REPORTS

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-png-payload"


class FakeStorage:
    """In-memory storage adapter for tests."""

    backend_name = "fake"

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def save(self, content: bytes, filename: str, context: str) -> StoredFile:
        key = f"{context}/{len(self.files)}-{filename}"
        self.files[key] = content
        return StoredFile(storage_backend=self.backend_name, storage_key=key)

    def delete(self, storage_key: str) -> None:
        self.files.pop(storage_key, None)

    def read(self, storage_key: str) -> bytes:
        if storage_key not in self.files:
            raise NotFoundError("Attachment file not found")
        return self.files[storage_key]

    def restore(self, storage_key: str, content: bytes) -> None:
        self.files[storage_key] = content

    def get_path(self, storage_key: str) -> Path:
        raise NotFoundError("Attachment file not found")


@pytest.fixture
def storage(api_client):
    fake = FakeStorage()
    api_client.app.dependency_overrides[get_attachment_storage] = lambda: fake
    yield fake
    api_client.app.dependency_overrides.pop(get_attachment_storage, None)


def test_submit_and_resolve_bug_report_flow(api_client, storage) -> None:
    submitted = api_client.post(
        "/api/v1/bug-reports",
        data={
            "title": "Nie działa zapis grupy",
            "description": "Po kliknięciu Zapisz nic się nie dzieje.",
        },
        files={"file": ("zrzut.png", io.BytesIO(PNG_BYTES), "image/png")},
    )
    assert submitted.status_code == 200
    report = submitted.json()
    assert report["status"] == "NOWY"
    assert report["reporter_email"] == "admin@example.com"
    assert report["original_filename"] == "zrzut.png"
    assert report["size_bytes"] == len(PNG_BYTES)

    listing = api_client.get("/api/v1/bug-reports").json()
    assert [item["id"] for item in listing] == [report["id"]]

    mine = api_client.get("/api/v1/bug-reports/my").json()
    assert [item["id"] for item in mine] == [report["id"]]

    resolved = api_client.patch(
        f"/api/v1/bug-reports/{report['id']}",
        json={"status": "ROZWIĄZANY", "resolution_comment": "Naprawione w PAP-79."},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "ROZWIĄZANY"
    assert resolved.json()["resolution_comment"] == "Naprawione w PAP-79."

    filtered = api_client.get(
        "/api/v1/bug-reports", params={"status": "ROZWIĄZANY"}
    ).json()
    assert len(filtered) == 1
    empty = api_client.get("/api/v1/bug-reports", params={"status": "NOWY"}).json()
    assert empty == []


def test_submit_without_file(api_client, storage) -> None:
    response = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Literówka na dashboardzie"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["original_filename"] is None
    assert body["description"] == ""


def test_file_download_roundtrip(api_client, storage) -> None:
    submitted = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Błąd z logiem"},
        files={"file": ("app.log", io.BytesIO(b"traceback..."), "text/plain")},
    ).json()

    download = api_client.get(f"/api/v1/bug-reports/{submitted['id']}/file")
    assert download.status_code == 200
    assert download.content == b"traceback..."
    assert 'filename="app.log"' in download.headers["content-disposition"]


def test_manager_deletes_report_with_attachment(api_client, storage) -> None:
    """PAP-94: a manager deletes any report; the stored file goes with it."""
    submitted = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Do usunięcia"},
        files={"file": ("zrzut.png", io.BytesIO(PNG_BYTES), "image/png")},
    ).json()
    assert storage.files != {}

    deleted = api_client.delete(f"/api/v1/bug-reports/{submitted['id']}")
    assert deleted.status_code == 204
    assert storage.files == {}
    assert api_client.get(f"/api/v1/bug-reports/{submitted['id']}").status_code == 404


def test_reporter_deletes_only_own_report(
    api_client, storage, db_session, admin_user
) -> None:
    """PAP-94: a reporter without manage permission deletes only own reports."""
    foreign = api_client.post(
        "/api/v1/bug-reports", data={"title": "Cudze zgłoszenie"}
    ).json()

    regular = User(
        username="zgłaszający",
        email="reporter@example.com",
        hashed_password="not-used",
        status="regular",
        is_active=True,
    )
    db_session.add(regular)
    db_session.flush()
    submit_perm = (
        db_session.query(Permission).filter_by(code=CAN_SUBMIT_BUG_REPORTS).one()
    )
    reporter_group = UserGroup(
        name="Zgłaszający",
        description="Może zgłaszać błędy, bez zarządzania",
        permissions=[submit_perm],
    )
    db_session.add(reporter_group)
    db_session.flush()
    db_session.execute(
        security_user_groups.insert(),
        {"user_id": regular.id, "group_id": reporter_group.id},
    )
    db_session.commit()
    api_client.app.dependency_overrides[get_current_user] = lambda: regular
    try:
        own = api_client.post(
            "/api/v1/bug-reports", data={"title": "Moje zgłoszenie"}
        ).json()

        assert (
            api_client.delete(f"/api/v1/bug-reports/{foreign['id']}").status_code == 403
        )
        assert api_client.delete(f"/api/v1/bug-reports/{own['id']}").status_code == 204
    finally:
        api_client.app.dependency_overrides[get_current_user] = lambda: admin_user

    assert api_client.get(f"/api/v1/bug-reports/{foreign['id']}").status_code == 200


def test_unknown_report_endpoints_return_404(api_client, storage) -> None:
    """Reading, updating or deleting a missing report is a clean 404."""
    assert api_client.get("/api/v1/bug-reports/999999").status_code == 404
    assert (
        api_client.patch(
            "/api/v1/bug-reports/999999", json={"status": "W_TRAKCIE"}
        ).status_code
        == 404
    )
    assert api_client.delete("/api/v1/bug-reports/999999").status_code == 404


def test_mp4_masquerading_as_heic_rejected(api_client, storage) -> None:
    mp4_header = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 16
    response = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Wideo udające zdjęcie"},
        files={"file": ("zdjecie.heic", io.BytesIO(mp4_header), "image/heic")},
    )
    assert response.status_code == 422
    assert storage.files == {}


def test_zip_upload_valid_and_path_traversal(api_client, storage) -> None:
    valid = io.BytesIO()
    with zipfile.ZipFile(valid, "w") as archive:
        archive.writestr("logs/app.log", "traceback...")
    accepted = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Paczka logów"},
        files={"file": ("logi.zip", io.BytesIO(valid.getvalue()), "application/zip")},
    )
    assert accepted.status_code == 200

    hostile = io.BytesIO()
    with zipfile.ZipFile(hostile, "w") as archive:
        archive.writestr("../evil.txt", "x")
    rejected = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Zip z traversal"},
        files={"file": ("zly.zip", io.BytesIO(hostile.getvalue()), "application/zip")},
    )
    assert rejected.status_code == 422


def test_utf16_log_upload_accepted(api_client, storage) -> None:
    content = "Wyjątek: NullReferenceException".encode("utf-16")
    response = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Log z PowerShella"},
        files={"file": ("app.log", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["original_filename"] == "app.log"


def test_download_missing_file_returns_404(api_client, storage) -> None:
    submitted = api_client.post(
        "/api/v1/bug-reports", data={"title": "Bez załącznika"}
    ).json()
    response = api_client.get(f"/api/v1/bug-reports/{submitted['id']}/file")
    assert response.status_code == 404


def test_rejects_bad_file_type_size_and_status(api_client, storage) -> None:
    bad_type = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Zły plik"},
        files={"file": ("wirus.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
    )
    assert bad_type.status_code == 422
    assert storage.files == {}

    too_big = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Za duży"},
        files={
            "file": ("duzy.png", io.BytesIO(b"x" * (10 * 1024 * 1024 + 1)), "image/png")
        },
    )
    assert too_big.status_code == 422

    masquerading = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "Skrypt udający obrazek"},
        files={"file": ("obrazek.png", io.BytesIO(b"#!/bin/sh\nrm -rf"), "image/png")},
    )
    assert masquerading.status_code == 422
    assert storage.files == {}

    blank_title = api_client.post(
        "/api/v1/bug-reports",
        data={"title": "   "},
    )
    assert blank_title.status_code == 422

    submitted = api_client.post(
        "/api/v1/bug-reports", data={"title": "Poprawny"}
    ).json()
    bad_status = api_client.patch(
        f"/api/v1/bug-reports/{submitted['id']}", json={"status": "ZAMKNIĘTY"}
    )
    assert bad_status.status_code == 422
