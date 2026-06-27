from functools import lru_cache

from pydantic_settings import BaseSettings

from app.core.constants import ATTACHMENT_MAX_SIZE_BYTES


class Settings(BaseSettings):
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
    attachment_max_size_bytes: int = ATTACHMENT_MAX_SIZE_BYTES

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[misc]
