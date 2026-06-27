from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.core.errors import NotFoundError, ValidationException
from app.modules.attachments.services.attachments import AttachmentService
from app.modules.attachments.storage import StoredFile


class FakeStorage:
    def __init__(self) -> None:
        self.saved: list[tuple[bytes, str, str]] = []
        self.deleted: list[str] = []
        self.files: dict[str, bytes] = {}

    def save(self, content: bytes, filename: str, context: str) -> StoredFile:
        self.saved.append((content, filename, context))
        self.files["fake/key.pdf"] = content
        return StoredFile(storage_backend="fake", storage_key="fake/key.pdf")

    def delete(self, storage_key: str) -> None:
        self.deleted.append(storage_key)
        self.files.pop(storage_key, None)

    def read(self, storage_key: str) -> bytes:
        try:
            return self.files[storage_key]
        except KeyError as exc:
            raise NotFoundError("Attachment file not found") from exc

    def restore(self, storage_key: str, content: bytes) -> None:
        self.files[storage_key] = content

    def get_path(self, storage_key: str):
        raise NotImplementedError


def build_service(repo: MagicMock, storage: FakeStorage) -> AttachmentService:
    service = AttachmentService.__new__(AttachmentService)
    service.session = MagicMock()
    service.storage = storage
    service.max_size_bytes = 10
    service.repo = repo
    return service


def test_create_bo_card_rejects_unsupported_file_type() -> None:
    repo = MagicMock()
    storage = FakeStorage()
    service = build_service(repo, storage)

    with pytest.raises(ValidationException):
        service.create_bo_card(
            group_id=1,
            beneficiary_id=2,
            volunteer_id=3,
            period="2026-06",
            filename="karta.txt",
            content_type="text/plain",
            content=b"abc",
            actor=SimpleNamespace(id=7, username="admin"),
        )

    repo.create.assert_not_called()
    assert storage.saved == []


def test_create_bo_card_saves_file_and_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = MagicMock()
    storage = FakeStorage()
    service = build_service(repo, storage)
    attachment = SimpleNamespace(id=1)
    repo.create.return_value = attachment
    validate_scope = MagicMock()
    monkeypatch.setattr(service, "_validate_bo_card_scope", validate_scope)

    result = service.create_bo_card(
        group_id=1,
        beneficiary_id=2,
        volunteer_id=3,
        period="2026-6",
        filename="karta.pdf",
        content_type="application/pdf",
        content=b"pdf",
        actor=SimpleNamespace(id=7, username="admin"),
        display_name="Czerwiec",
    )

    assert result is attachment
    validate_scope.assert_called_once_with(1, 2, 3)
    assert storage.saved == [(b"pdf", "karta.pdf", "bo_card")]
    repo.create.assert_called_once()
    payload = repo.create.call_args.kwargs
    assert payload["context"] == "bo_card"
    assert payload["period"] == "2026-06"
    assert payload["display_name"] == "Czerwiec"
    assert payload["created_by_id"] == 7
    assert payload["updated_by_username"] == "admin"
    service.session.commit.assert_called_once()


def test_scope_validation_uses_domain_repositories() -> None:
    service = build_service(MagicMock(), FakeStorage())
    service.group_repo = MagicMock()
    service.beneficiary_repo = MagicMock()
    service.volunteer_repo = MagicMock()
    service.assignment_repo = MagicMock()
    service.group_repo.get_by_id.return_value = SimpleNamespace(id=1)
    service.beneficiary_repo.get_by_id.return_value = SimpleNamespace(
        id=2,
        group_id=1,
    )
    service.volunteer_repo.get_by_id.return_value = SimpleNamespace(id=3)
    service.assignment_repo.get_by_beneficiary_volunteer.return_value = SimpleNamespace(
        id=4
    )

    service._validate_bo_card_scope(1, 2, 3)

    service.group_repo.get_by_id.assert_called_once_with(1)
    service.beneficiary_repo.get_by_id.assert_called_once_with(2)
    service.volunteer_repo.get_by_id.assert_called_once_with(3)
    service.assignment_repo.get_by_beneficiary_volunteer.assert_called_once_with(2, 3)
    service.session.query.assert_not_called()


def test_delete_attachment_removes_file_before_committing_metadata() -> None:
    repo = MagicMock()
    storage = FakeStorage()
    storage.files["fake/key.pdf"] = b"pdf"
    repo.get_by_id.return_value = SimpleNamespace(storage_key="fake/key.pdf")
    service = build_service(repo, storage)

    service.delete_attachment(1)

    assert storage.deleted == ["fake/key.pdf"]
    assert storage.files == {}
    repo.delete.assert_called_once_with(repo.get_by_id.return_value)
    service.session.commit.assert_called_once()


def test_delete_attachment_restores_file_when_commit_fails() -> None:
    repo = MagicMock()
    storage = FakeStorage()
    storage.files["fake/key.pdf"] = b"pdf"
    repo.get_by_id.return_value = SimpleNamespace(storage_key="fake/key.pdf")
    service = build_service(repo, storage)
    service.session.commit.side_effect = RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.delete_attachment(1)

    assert storage.files["fake/key.pdf"] == b"pdf"
    service.session.rollback.assert_called_once()


def test_delete_attachment_removes_metadata_when_file_is_already_missing() -> None:
    repo = MagicMock()
    storage = FakeStorage()
    repo.get_by_id.return_value = SimpleNamespace(storage_key="missing.pdf")
    service = build_service(repo, storage)

    service.delete_attachment(1)

    repo.delete.assert_called_once_with(repo.get_by_id.return_value)
    service.session.commit.assert_called_once()
