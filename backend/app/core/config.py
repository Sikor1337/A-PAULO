from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    # Database - required, must be set in .env
    database_url: str
    # Database schema name (default: public)
    database_schema: str = "public"

    # JWT
    secret_key: str
    access_token_expire_minutes: int = 120
    algorithm: str = "HS256"

    # Attachments
    attachment_storage_path: str = "storage/attachments"

    # Email (PAP-87): "console" logs instead of sending (dev/tests),
    # "resend" sends through the Resend HTTP API (see docs/pap-86-email-spike.md).
    email_provider: str = "console"
    resend_api_key: str = ""
    email_from: str = "A-PAULO <onboarding@resend.dev>"
    frontend_base_url: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[misc]
