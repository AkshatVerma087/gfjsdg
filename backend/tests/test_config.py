"""Tests for typed configuration layer (P1-T03)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from config.env import Settings, settings


def test_settings_loaded_with_valid_defaults():
    """Settings should load successfully with valid defaults or environment."""
    assert settings.django_env in ("development", "production", "test")
    assert isinstance(settings.allowed_hosts_list, list)
    assert len(settings.allowed_hosts_list) > 0
    assert settings.default_cutoff_time == "11:00"


def test_secrets_are_redacted_in_repr():
    """Secrets must never be printed in repr(settings)."""
    settings_repr = repr(settings)
    raw_secret = settings.django_secret_key.get_secret_value()
    assert raw_secret not in settings_repr
    assert "**********" in settings_repr or "SecretStr" in settings_repr


def test_invalid_database_url_raises_error():
    """Invalid database URL scheme must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            DJANGO_SECRET_KEY="test-secret-key-12345",
            DATABASE_URL="mysql://invalid:3306/db",
        )
    assert "DATABASE_URL must start with postgresql://, postgres://, or sqlite://" in str(
        exc_info.value
    )


def test_invalid_cutoff_time_raises_error():
    """Invalid cutoff time format must be rejected."""
    with pytest.raises(ValidationError):
        Settings(
            DJANGO_SECRET_KEY="test-secret-key-12345",
            DEFAULT_CUTOFF_TIME="25:99",
        )


def test_env_var_override(monkeypatch):
    """Real environment variables should override default values."""
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "custom.domain.com,api.domain.com")
    monkeypatch.setenv("DEFAULT_CUTOFF_TIME", "09:30")
    custom_settings = Settings()
    assert custom_settings.allowed_hosts_list == ["custom.domain.com", "api.domain.com"]
    assert custom_settings.default_cutoff_time == "09:30"


def test_no_os_environ_reads_outside_env_py():
    """Project code outside config/env.py and wsgi/manage must not directly read os.environ."""
    backend_dir = Path(__file__).resolve().parent.parent
    violations = []

    # Exclude manage.py and wsgi.py which setdefault DJANGO_SETTINGS_MODULE per standard Django convention
    allowed_files = {"env.py", "manage.py", "wsgi.py", "conftest.py"}

    for py_file in backend_dir.rglob("*.py"):
        if py_file.name in allowed_files or "tests" in py_file.parts:
            continue
        content = py_file.read_text(encoding="utf-8")
        if "os.environ" in content or "os.getenv" in content:
            violations.append(str(py_file.relative_to(backend_dir)))

    assert violations == [], f"Direct os.environ reads found in: {violations}"
