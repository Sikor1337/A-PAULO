"""Stable opaque access link for account-bound recruitment."""

import hashlib
import hmac

from app.core.config import get_settings
from app.modules.recruitment.constants import RECRUITMENT_ROUTE_PREFIX

_TOKEN_PURPOSE = b"a-paulo-recruitment-application-link-v1"


def get_recruitment_access_token() -> str:
    """Derive a stable URL-safe token without storing or exposing SECRET_KEY."""

    secret = get_settings().secret_key.encode("utf-8")
    return hmac.new(secret, _TOKEN_PURPOSE, hashlib.sha256).hexdigest()


def is_valid_recruitment_access_token(token: str | None) -> bool:
    if not token:
        return False
    return hmac.compare_digest(token, get_recruitment_access_token())


def get_recruitment_frontend_path() -> str:
    return f"{RECRUITMENT_ROUTE_PREFIX}/{get_recruitment_access_token()}"
