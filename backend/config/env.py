"""Typed configuration layer for Wind Forecast Monitor.

Follows the boilerplate pattern:
1. Environment variables override .env file.
2. Typed and validated at boot using pydantic-settings.
3. Secrets are typed as SecretStr and never leaked in repr() or logs.
4. Fails fast with clear error messages if required configuration is missing.
"""

from datetime import date, time
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
ENV_FILE_PATH = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Application settings schema."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH) if ENV_FILE_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment & Debug
    django_env: Literal["development", "production", "test"] = Field(
        default="development",
        validation_alias="DJANGO_ENV",
    )
    django_debug: bool = Field(
        default=False,
        validation_alias="DJANGO_DEBUG",
    )

    # Secret key (required in production; safe placeholder only in dev/test)
    django_secret_key: SecretStr = Field(
        default=SecretStr("insecure-dev-secret-key-change-in-production-only-placeholder-12345"),
        validation_alias="DJANGO_SECRET_KEY",
    )

    # Hosts & Origins
    django_allowed_hosts: str = Field(
        default="localhost,127.0.0.1,0.0.0.0",
        validation_alias="DJANGO_ALLOWED_HOSTS",
    )

    # Persistence
    database_url: str = Field(
        default="postgresql://wind_user:wind_password@localhost:5432/wind_forecast_db",
        validation_alias="DATABASE_URL",
    )

    # Elexon BMRS API
    elexon_base_url: str = Field(
        default="https://data.elexon.co.uk/bmrs/api/v1",
        validation_alias="ELEXON_BASE_URL",
    )
    elexon_timeout_seconds: int = Field(
        default=15,
        validation_alias="ELEXON_TIMEOUT_SECONDS",
    )

    # Domain Timing & Windows
    default_cutoff_time: str = Field(
        default="11:00",
        validation_alias="DEFAULT_CUTOFF_TIME",
    )
    data_window_start: date = Field(
        default=date(2025, 12, 30),
        validation_alias="DATA_WINDOW_START",
    )
    data_window_end: date = Field(
        default=date(2026, 2, 3),
        validation_alias="DATA_WINDOW_END",
    )
    default_window_start: date = Field(
        default=date(2026, 1, 2),
        validation_alias="DEFAULT_WINDOW_START",
    )
    default_window_end: date = Field(
        default=date(2026, 2, 1),
        validation_alias="DEFAULT_WINDOW_END",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        v_clean = v.strip()
        valid_schemes = ("postgresql://", "postgres://", "sqlite://")
        if not any(v_clean.startswith(prefix) for prefix in valid_schemes):
            raise ValueError(
                f"DATABASE_URL must start with postgresql://, postgres://, or sqlite:// (got '{v_clean.split('://')[0]}://...')"
            )
        return v_clean

    @field_validator("default_cutoff_time")
    @classmethod
    def validate_cutoff_time(cls, v: str) -> str:
        parts = v.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"DEFAULT_CUTOFF_TIME must be in HH:MM format (got '{v}')")
        try:
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except ValueError:
            raise ValueError(
                f"DEFAULT_CUTOFF_TIME must be a valid time 00:00-23:59 (got '{v}')"
            ) from None
        return f"{h:02d}:{m:02d}"

    @property
    def is_production(self) -> bool:
        return self.django_env == "production"

    @property
    def is_development(self) -> bool:
        return self.django_env == "development"

    @property
    def is_test(self) -> bool:
        return self.django_env == "test"

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.django_allowed_hosts.split(",") if h.strip()]

    @property
    def parsed_cutoff_time(self) -> time:
        h, m = map(int, self.default_cutoff_time.split(":"))
        return time(hour=h, minute=m)


def load_settings() -> Settings:
    """Load and validate settings, failing fast on invalid configuration."""
    try:
        s = Settings()
        if s.is_production and "insecure-dev-secret-key" in s.django_secret_key.get_secret_value():
            raise ValueError("DJANGO_SECRET_KEY must be configured with a production secret")
        return s
    except Exception as exc:
        raise RuntimeError(f"Application configuration error: {exc}") from None


# Global immutable settings instance
settings = load_settings()
