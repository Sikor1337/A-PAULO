"""Storage adapters for file attachments."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.core.errors import NotFoundError


@dataclass(frozen=True)
class StoredFile:
    """Result of persisting a file in a storage backend."""

    storage_backend: str
    storage_key: str


class AttachmentStorage(Protocol):
    """Storage contract used by attachment services."""

    def save(self, content: bytes, filename: str, context: str) -> StoredFile:
        """Persist bytes and return an opaque storage key."""

    def delete(self, storage_key: str) -> None:
        """Delete bytes for the given storage key."""

    def get_path(self, storage_key: str) -> Path:
        """Return a local path for backends that can serve files directly."""


class LocalAttachmentStorage:
    """Local filesystem storage for attachments."""

    backend_name = "local"

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, filename: str, context: str) -> StoredFile:
        suffix = Path(filename).suffix.lower()
        safe_context = self._safe_part(context) or "attachments"
        storage_key = f"{safe_context}/{uuid4().hex}{suffix}"
        path = self._resolve_key(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return StoredFile(storage_backend=self.backend_name, storage_key=storage_key)

    def delete(self, storage_key: str) -> None:
        path = self._resolve_key(storage_key)
        if path.exists():
            path.unlink()

    def get_path(self, storage_key: str) -> Path:
        path = self._resolve_key(storage_key)
        if not path.exists():
            raise NotFoundError("Attachment file not found")
        return path

    def _resolve_key(self, storage_key: str) -> Path:
        path = (self.base_path / Path(storage_key)).resolve()
        if not path.is_relative_to(self.base_path):
            raise NotFoundError("Attachment file not found")
        return path

    @staticmethod
    def _safe_part(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
