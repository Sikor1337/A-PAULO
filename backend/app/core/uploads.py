"""Shared validation helpers for uploaded files."""

from app.core.constants import MEGABYTE
from app.core.errors import ValidationException


def ensure_upload_size(data: bytes, max_bytes: int) -> None:
    """Reject an uploaded file larger than ``max_bytes``."""
    if len(data) > max_bytes:
        raise ValidationException(
            f"Plik jest zbyt duży (maksymalnie {max_bytes // MEGABYTE} MB)"
        )
