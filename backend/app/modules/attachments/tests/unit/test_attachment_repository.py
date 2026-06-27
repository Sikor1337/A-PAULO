"""Unit tests for attachment metadata repository."""

from unittest.mock import MagicMock

from app.modules.attachments.models import Attachment
from app.modules.attachments.repositories import AttachmentRepository


def test_get_by_id_uses_session_identity_lookup() -> None:
    session = MagicMock()
    expected = MagicMock(spec=Attachment)
    session.get.return_value = expected

    result = AttachmentRepository(session).get_by_id(42)

    assert result is expected
    session.get.assert_called_once_with(Attachment, 42)
