"""Integration tests for the bug reports module (PAP-83)."""

import io
from pathlib import Path

import pytest

from app.core.dependencies import get_attachment_storage
from app.core.errors import NotFoundError
from app.infrastructure.storage.attachments import StoredFile

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
