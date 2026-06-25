import base64
import hashlib
from datetime import timedelta

from app.modules.security.services.password import hash_password, verify_password
from app.modules.security.services.token import TokenService


def test_hash_password_creates_verifiable_bcrypt_hash() -> None:
    hashed = hash_password("StrongPass123")

    assert hashed != "StrongPass123"
    assert verify_password("StrongPass123", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_supports_legacy_pbkdf2_hashes() -> None:
    salt = "testsalt"
    iterations = 1200
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        b"StrongPass123",
        salt.encode("utf-8"),
        iterations,
    )
    encoded = base64.b64encode(digest).decode("utf-8")

    assert (
        verify_password(
            "StrongPass123",
            f"pbkdf2_sha256${iterations}${salt}${encoded}",
        )
        is True
    )
    assert (
        verify_password(
            "wrong-password",
            f"pbkdf2_sha256${iterations}${salt}${encoded}",
        )
        is False
    )


def test_token_service_round_trips_access_and_refresh_payloads() -> None:
    service = TokenService(
        secret_key="test-secret",
        access_token_expire_minutes=5,
    )

    access = service.create_access_token(
        {"sub": "42"},
        expires_delta=timedelta(minutes=1),
    )
    refresh = service.create_refresh_token({"sub": "42"})

    assert service.decode_token(access)["type"] == "access"
    assert service.decode_token(access)["sub"] == "42"
    assert service.decode_token(refresh)["type"] == "refresh"


def test_token_service_returns_none_for_invalid_token() -> None:
    service = TokenService(secret_key="test-secret")

    assert service.decode_token("not-a-jwt") is None
