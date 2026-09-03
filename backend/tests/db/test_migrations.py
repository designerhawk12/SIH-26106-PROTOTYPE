"""Alembic migration tests that require no live PostgreSQL service."""

from __future__ import annotations

import io
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).parents[3]
ALEMBIC_CONFIG = ROOT / "backend" / "alembic.ini"


def _config(*, output_buffer: io.StringIO | None = None) -> Config:
    return Config(str(ALEMBIC_CONFIG), output_buffer=output_buffer)


def test_initial_migration_upgrades_fresh_sqlite_database(
    tmp_path: Path, monkeypatch,
) -> None:
    database_path = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    command.upgrade(_config(), "head")

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    try:
        inspector = inspect(engine)
        assert {"alembic_version", "cases", "user_profiles"}.issubset(
            inspector.get_table_names()
        )
        assert {column["name"] for column in inspector.get_columns("cases")} == {
            "id",
            "created_at",
            "updated_at",
            "status",
            "filename",
            "email_sha256",
            "risk_score",
            "severity",
            "analysis_json",
        }
        assert {index["name"] for index in inspector.get_indexes("cases")} == {
            "ix_cases_created_at",
            "ix_cases_email_sha256",
            "ix_cases_status",
        }
        assert {column["name"] for column in inspector.get_columns("user_profiles")} == {
            "user_id",
            "display_name",
            "email",
            "organization",
            "role",
            "created_at",
            "updated_at",
        }
    finally:
        engine.dispose()


def test_postgresql_migration_can_render_offline(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@db.example.test:5432/postgres?sslmode=require",
    )
    output = io.StringIO()
    command.upgrade(_config(output_buffer=output), "head", sql=True)
    sql = output.getvalue()
    assert "CREATE TABLE cases" in sql
    assert "CREATE TABLE user_profiles" in sql
    assert "UUID" in sql
    assert "JSON" in sql
