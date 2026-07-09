"""Shared field validators reused by schemas and services."""

from pydantic import EmailStr, TypeAdapter, ValidationError

_EMAIL_ADAPTER: TypeAdapter[str] = TypeAdapter(EmailStr)


def is_valid_email(value: str) -> bool:
    """Check an email address with the same rules as ``EmailStr`` schemas."""
    try:
        _EMAIL_ADAPTER.validate_python(value)
    except ValidationError:
        return False
    return True
