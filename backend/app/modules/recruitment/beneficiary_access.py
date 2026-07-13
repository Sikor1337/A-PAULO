"""Stable public link and short-lived submission proof for PAP-90."""

import hashlib
import hmac
import time

from app.core.config import get_settings
from app.modules.recruitment.beneficiary_constants import (
    BENEFICIARY_RECRUITMENT_ROUTE_PREFIX,
)

_LINK_PURPOSE = b"a-paulo-beneficiary-recruitment-link-v1"
_FORM_PURPOSE = b"a-paulo-beneficiary-recruitment-form-v1"
_FORM_TOKEN_MAX_AGE_SECONDS = 2 * 60 * 60


def _sign(payload: bytes, purpose: bytes) -> str:
    secret = get_settings().secret_key.encode("utf-8")
    return hmac.new(secret, purpose + b":" + payload, hashlib.sha256).hexdigest()


def get_beneficiary_access_token() -> str:
    return _sign(b"public", _LINK_PURPOSE)


def is_valid_beneficiary_access_token(token: str | None) -> bool:
    return token is not None and hmac.compare_digest(
        token, get_beneficiary_access_token()
    )


def get_beneficiary_frontend_path() -> str:
    return f"{BENEFICIARY_RECRUITMENT_ROUTE_PREFIX}/{get_beneficiary_access_token()}"


def create_form_token() -> str:
    timestamp = str(int(time.time()))
    return f"{timestamp}.{_sign(timestamp.encode(), _FORM_PURPOSE)}"


def is_valid_form_token(token: str) -> bool:
    try:
        timestamp_text, signature = token.split(".", 1)
        timestamp = int(timestamp_text)
    except (ValueError, AttributeError):
        return False
    age = int(time.time()) - timestamp
    if age < 0 or age > _FORM_TOKEN_MAX_AGE_SECONDS:
        return False
    expected = _sign(timestamp_text.encode(), _FORM_PURPOSE)
    return hmac.compare_digest(signature, expected)
