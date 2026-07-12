from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # A deployment may retain variables used by an older/newer application
    # version. They must not prevent the backend from starting after a rollback.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[misc]
