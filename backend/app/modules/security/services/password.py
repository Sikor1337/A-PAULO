import base64
import hashlib
import hmac

import bcrypt


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_bcrypt(plain: str, hashed: str) -> bool:
    """Verify bcrypt hashed password."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _verify_pbkdf2_sha256(plain: str, encoded: str) -> bool:
    """Verify pbkdf2_sha256$<iterations>$<salt>$<hash> format."""
    try:
        _, iterations_str, salt, hash_b64 = encoded.split("$", 3)
        iterations = int(iterations_str)
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt.encode("utf-8"), iterations)
        expected = base64.b64encode(dk).decode("utf-8")
        return hmac.compare_digest(expected, hash_b64)
    except Exception:
        return False


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash (supports both bcrypt and pbkdf2)."""
    if hashed.startswith("pbkdf2_sha256$"):
        return _verify_pbkdf2_sha256(plain, hashed)
    return _verify_bcrypt(plain, hashed)
