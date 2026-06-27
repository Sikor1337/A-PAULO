"""Unit tests for attachment storage infrastructure."""

from app.infrastructure.storage.factory import AttachmentStorageFactory


def test_factory_reuses_storage_for_equivalent_path(tmp_path) -> None:
    factory = AttachmentStorageFactory()

    first = factory.get_or_create_local_storage(tmp_path)
    second = factory.get_or_create_local_storage(tmp_path / ".")

    assert first is second


def test_factory_clear_discards_cached_storage(tmp_path) -> None:
    factory = AttachmentStorageFactory()
    first = factory.get_or_create_local_storage(tmp_path)

    factory.clear()
    second = factory.get_or_create_local_storage(tmp_path)

    assert first is not second
