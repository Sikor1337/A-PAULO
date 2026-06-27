"""Application-wide constants."""

from typing import Final, Literal, get_args

ATTACHMENT_MAX_SIZE_BYTES: Final = 10 * 1024 * 1024
ATTACHMENT_ALLOWED_EXTENSIONS: Final = frozenset(
    {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
)
ATTACHMENT_ALLOWED_CONTENT_TYPES: Final = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
    }
)
ATTACHMENT_FALLBACK_CONTENT_TYPES: Final = frozenset({"", "application/octet-stream"})
ATTACHMENT_SUPPORTED_FILES_MESSAGE: Final = (
    "Supported files: PDF, JPG, PNG, WEBP, HEIC, HEIF"
)
BO_CARD_CONTEXT: Final = "bo_card"
BO_CARD_PERIOD_PATTERN: Final = r"^\d{4}-(0[1-9]|1[0-2])$"

BOCardSortKey = Literal[
    "created_at",
    "updated_at",
    "period",
    "display_name",
    "group_name",
    "beneficiary_name",
    "volunteer_name",
    "size_bytes",
]
SortDirection = Literal["asc", "desc"]
BO_CARD_SORT_KEYS: Final = frozenset(get_args(BOCardSortKey))
