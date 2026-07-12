"""Settings loading regression tests."""

from pathlib import Path

import pytest

from app.core.config import Settings


def test_settings_ignore_variables_from_other_application_versions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DATABASE_URL=sqlite+pysqlite:///:memory:\n"
        "SECRET_KEY=test-key\n"
        "EMAIL_PROVIDER=resend\n"
        "RESEND_API_KEY=legacy-key\n"
        "EMAIL_FROM=mail@example.com\n"
        "FRONTEND_BASE_URL=http://localhost:5173\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    settings = Settings(_env_file=env_file)  # type: ignore[call-arg]

    assert settings.database_url == "sqlite+pysqlite:///:memory:"
    assert settings.secret_key == "test-key"
