"""Environment-backed application configuration."""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    """Immutable runtime settings loaded exclusively from environment variables."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    app_name: str = "email-threat-platform"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_log_level: str = "INFO"
    demo_mode: bool = False
    database_url: str = "sqlite:///./email_threat_platform.db"
    max_upload_bytes: int = Field(default=26_214_400, gt=0)

    allowed_origins: tuple[str, ...] = (
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )

    @classmethod
    def from_environment(cls) -> Settings:
        """Build settings without reading dotenv files or secret-bearing config files."""

        origins = tuple(
            origin.strip()
            for origin in os.getenv(
                "ALLOWED_ORIGINS",
                "http://localhost:8080,"
                "http://127.0.0.1:8080,"
                "http://localhost:5173,"
                "http://127.0.0.1:5173",
            ).split(",")
            if origin.strip()
        )

        demo_mode_value = os.getenv("DEMO_MODE", "false").strip().lower()
        if demo_mode_value not in {"true", "false"}:
            raise ValueError("DEMO_MODE must be either 'true' or 'false'.")

        return cls(
            app_name=os.getenv("APP_NAME", "email-threat-platform"),
            app_version=os.getenv("APP_VERSION", "0.1.0"),
            app_env=os.getenv("APP_ENV", "development"),
            app_log_level=os.getenv("APP_LOG_LEVEL", "INFO"),
            demo_mode=demo_mode_value == "true",
            database_url=os.getenv(
                "DATABASE_URL", "sqlite:///./email_threat_platform.db"
            ),
            max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", "26214400")),
            allowed_origins=origins,
        )


def get_settings() -> Settings:
    """Return a fresh environment snapshot for application construction."""

    return Settings.from_environment()
