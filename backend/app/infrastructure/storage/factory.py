"""Storage backend factory helpers."""

from pathlib import Path

from app.modules.attachments.storage import AttachmentStorage, LocalAttachmentStorage


class AttachmentStorageFactory:
    """Create and cache attachment storage backend instances."""

    def __init__(self) -> None:
        self._local_storages: dict[Path, AttachmentStorage] = {}

    def get_or_create_local_storage(
        self,
        base_path: str | Path,
    ) -> AttachmentStorage:
        """Return one local storage instance per normalized base path."""
        normalized_path = Path(base_path).resolve()
        storage = self._local_storages.get(normalized_path)
        if storage is None:
            storage = LocalAttachmentStorage(normalized_path)
            self._local_storages[normalized_path] = storage
        return storage

    def clear(self) -> None:
        """Clear cached storage instances, primarily for test isolation."""
        self._local_storages.clear()
