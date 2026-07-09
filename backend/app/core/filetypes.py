"""File-content sniffing so uploads must match their declared extension.

Extension checks alone do not stop a script or binary renamed to ".jpg";
these helpers verify the leading magic bytes of the actual content.
"""

import io
import zipfile
from collections.abc import Callable
from pathlib import PurePosixPath

_ZIP_PREFIXES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_UTF16_BOMS = (b"\xff\xfe", b"\xfe\xff")
# ISO-BMFF brands used by HEIC/HEIF images; other ftyp brands (mp4, mov)
# are containers masquerading as images.
_HEIF_BRANDS = (
    b"heic",
    b"heix",
    b"hevc",
    b"hevx",
    b"heim",
    b"heis",
    b"hevm",
    b"hevs",
    b"mif1",
    b"msf1",
)


def _is_pdf(content: bytes) -> bool:
    return content.startswith(b"%PDF-")


def _is_png(content: bytes) -> bool:
    return content.startswith(b"\x89PNG\r\n\x1a\n")


def _is_jpeg(content: bytes) -> bool:
    return content.startswith(b"\xff\xd8\xff")


def _is_webp(content: bytes) -> bool:
    return content[:4] == b"RIFF" and content[8:12] == b"WEBP"


def _is_heif(content: bytes) -> bool:
    return content[4:8] == b"ftyp" and content[8:12] in _HEIF_BRANDS


def _is_zip(content: bytes) -> bool:
    """Check it is a readable ZIP archive with no path-traversal entries."""
    if not content.startswith(_ZIP_PREFIXES):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            for name in archive.namelist():
                path = PurePosixPath(name.replace("\\", "/"))
                if path.is_absolute() or ".." in path.parts:
                    return False
    except zipfile.BadZipFile:
        return False
    return True


def _is_plain_text(content: bytes) -> bool:
    # UTF-16 text (e.g. PowerShell logs) is full of NUL bytes but legitimate;
    # accept it by its BOM instead of the NUL heuristic.
    if content.startswith(_UTF16_BOMS):
        return True
    return b"\x00" not in content


_CHECKS_BY_EXTENSION: dict[str, Callable[[bytes], bool]] = {
    ".pdf": _is_pdf,
    ".png": _is_png,
    ".jpg": _is_jpeg,
    ".jpeg": _is_jpeg,
    ".webp": _is_webp,
    ".heic": _is_heif,
    ".heif": _is_heif,
    ".zip": _is_zip,
    ".txt": _is_plain_text,
    ".log": _is_plain_text,
}


def content_matches_extension(extension: str, content: bytes) -> bool:
    """Check that file content looks like its extension claims.

    Extensions without a registered signature are accepted as-is.
    """
    check = _CHECKS_BY_EXTENSION.get(extension.lower())
    return check(content) if check else True
