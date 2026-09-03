"""Database configuration and persistence regression tests."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_case_repository
from backend.app.core import Settings
from backend.app.db import (
    SqlAlchemyCaseRepository,
    create_database_engine,
    create_session_factory,
    initialize_database,
    normalize_database_url,
)
from backend.app.db.base import Base
from backend.app.db.models import Case
from backend.app.schemas import (
    AnalysisStatus,
    EmailAnalysis,
    ExtractedIOC,
    IOCSource,
    IOCType,
    ParsedEmail,
    TimelineEvent,
    TimelineEventType,
)
from backend.app.services.export import build_export_service
from backend.app.services.reporting import build_reporting_service
from backend.main import create_app


def _partial_analysis() -> EmailAnalysis:
    timestamp = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)
    return EmailAnalysis(
        case_id=uuid4(),
        status=AnalysisStatus.PARTIAL,
        original_filename="partial.eml",
        created_at=timestamp,
        completed_at=timestamp,
        parsed_email=ParsedEmail(
            original_sha256="a" * 64,
            subject="Persisted evidence",
            iocs=(
                ExtractedIOC(
                    type=IOCType.DOMAIN,
                    value="evidence.example",
                    normalized_value="evidence.example",
                    source=IOCSource.BODY_TEXT,
                ),
            ),
        ),
        timeline=(
            TimelineEvent(
                sequence=0,
                event_type=TimelineEventType.ANALYSIS_COMPLETED,
                timestamp=timestamp,
                title="Partial analysis persisted",
                source="test",
                evidence_refs=("domain:evidence.example",),
            ),
        ),
        warnings=("Threat intelligence unavailable.",),
    )


def test_database_url_environment_and_sqlite_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert Settings.from_environment().database_url.startswith("sqlite")

    configured = "postgresql://user:password@db.example.test:5432/postgres?sslmode=require"
    monkeypatch.setenv("DATABASE_URL", configured)
    assert Settings.from_environment().database_url == configured


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://"])
def test_supabase_style_url_selects_psycopg3(scheme: str) -> None:
    normalized = normalize_database_url(f"{scheme}user:password@db.example.test/postgres")
    assert normalized.startswith("postgresql+psycopg://")
    engine = create_database_engine(normalized)
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
    finally:
        engine.dispose()


def test_case_model_compiles_for_postgresql() -> None:
    ddl = str(CreateTable(Case.__table__).compile(dialect=postgresql.dialect()))
    assert "CREATE TABLE cases" in ddl
    assert "UUID" in ddl
    assert "JSON" in ddl
    assert isinstance(Case.__table__.c.analysis_json.type, JSON)


def test_postgresql_startup_does_not_run_create_all(monkeypatch: pytest.MonkeyPatch) -> None:
    create_all = MagicMock()
    monkeypatch.setattr(Base.metadata, "create_all", create_all)
    engine = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    initialize_database(engine)  # type: ignore[arg-type]
    create_all.assert_not_called()


@pytest.mark.asyncio
async def test_partial_case_report_and_evidence_survive_persistence() -> None:
    engine = create_database_engine("sqlite://")
    initialize_database(engine)
    factory = create_session_factory(engine)
    submitted = _partial_analysis()

    with factory() as session:
        repository = SqlAlchemyCaseRepository(session)
        repository.create(submitted)
        restored = repository.get_analysis(submitted.case_id)

    assert restored == submitted
    assert restored is not None
    assert restored.status is AnalysisStatus.PARTIAL
    assert restored.timeline[0].evidence_refs == ("domain:evidence.example",)

    report = await build_reporting_service().render_pdf(restored)
    evidence = await build_export_service().export_case(restored)
    assert report.startswith(b"%PDF")
    with zipfile.ZipFile(io.BytesIO(evidence)) as archive:
        assert "analysis.json" in archive.namelist()
        assert "timeline.json" in archive.namelist()
        assert "iocs.json" in archive.namelist()
    engine.dispose()


def test_repository_rolls_back_failed_transaction() -> None:
    session = MagicMock(spec=Session)
    session.commit.side_effect = SQLAlchemyError("database unavailable")
    repository = SqlAlchemyCaseRepository(session)

    with pytest.raises(SQLAlchemyError):
        repository.create(_partial_analysis())

    session.rollback.assert_called_once_with()


def test_database_failure_returns_structured_503() -> None:
    class FailingRepository:
        def list(self, *, limit: int, offset: int) -> tuple[Case, ...]:
            del limit, offset
            raise SQLAlchemyError("connection failed")

    engine = create_database_engine("sqlite://")
    app = create_app(
        settings=Settings(database_url="sqlite://"),
        database_engine=engine,
    )

    def override_repository():
        yield FailingRepository()

    app.dependency_overrides[get_case_repository] = override_repository
    with TestClient(app) as client:
        response = client.get("/api/v1/cases")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "connection failed" not in response.text


def test_sqlite_schema_and_retrieval_remain_available() -> None:
    engine = create_database_engine("sqlite://")
    initialize_database(engine)
    assert "cases" in inspect(engine).get_table_names()

    factory = create_session_factory(engine)
    submitted = _partial_analysis()
    with factory() as session:
        repository = SqlAlchemyCaseRepository(session)
        repository.create(submitted)
        assert repository.get_analysis(submitted.case_id) == submitted
    engine.dispose()
