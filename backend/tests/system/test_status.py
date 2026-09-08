"""Tests for the sanitized, administrator-only system status endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.core import Settings
from backend.app.db import SqlAlchemyUserProfileRepository, create_database_engine
from backend.app.schemas import UserRole
from backend.app.services.system_status import build_system_status
from backend.main import create_app
from backend.tests.auth_helpers import AUTH_HEADERS, TEST_USER_ID, FakeIdentityVerifier


def _app(*, settings: Settings) -> object:
    return create_app(
        settings=settings,
        database_engine=create_database_engine("sqlite://"),
        identity_verifier=FakeIdentityVerifier(),
    )


def test_status_is_sanitized_and_reports_configured_postgres_components(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ABUSEIPDB_API_KEY", "abuse-secret-value")
    monkeypatch.setenv("VIRUSTOTAL_API_KEY", "virustotal-secret-value")
    settings = Settings(
        database_url="postgresql://user:database-secret@project.supabase.co:5432/postgres",
        supabase_url="https://project.supabase.co",
        supabase_publishable_key="publishable-key",
        groq_api_key=SecretStr("groq-secret-value"),
        demo_mode=True,
    )

    status = build_system_status(settings)
    serialized = status.model_dump_json()

    assert status.database.label == "Supabase PostgreSQL"
    assert status.database.state == "OPERATIONAL"
    assert status.authentication.state == "CONFIGURED"
    assert status.demo_mode.state == "ENABLED"
    assert status.geolocation.state == "SIMULATED"
    assert status.ai_investigator.label == "AI Investigator (Groq)"
    assert status.ai_investigator.state == "CONFIGURED"
    assert {item.label: item.state for item in status.threat_intelligence} == {
        "AbuseIPDB": "CONFIGURED",
        "VirusTotal": "CONFIGURED",
    }
    for secret in ("database-secret", "publishable-key", "groq-secret-value", "abuse-secret-value", "virustotal-secret-value"):
        assert secret not in serialized


def test_status_reports_unconfigured_components_without_claiming_safety(monkeypatch) -> None:
    monkeypatch.delenv("ABUSEIPDB_API_KEY", raising=False)
    monkeypatch.delenv("VIRUSTOTAL_API_KEY", raising=False)

    status = build_system_status(Settings(database_url="sqlite://"))

    assert status.database.label == "SQLite Development Fallback"
    assert status.authentication.state == "NOT_CONFIGURED"
    assert status.demo_mode.state == "DISABLED"
    assert status.ai_investigator.state == "NOT_CONFIGURED"
    assert all(item.state == "NOT_CONFIGURED" for item in status.threat_intelligence)
    assert all("safe" not in item.detail.casefold() for item in status.threat_intelligence)


def test_system_status_requires_administrator_permission() -> None:
    app = _app(settings=Settings(database_url="sqlite://"))
    with TestClient(app) as client:
        unauthenticated = client.get("/api/v1/system/status")
    with TestClient(app, headers=AUTH_HEADERS) as client:
        assert client.get("/api/v1/auth/me").status_code == 200
        analyst = client.get("/api/v1/system/status")
        with app.state.session_factory() as session:
            SqlAlchemyUserProfileRepository(session).update_role(TEST_USER_ID, UserRole.ADMIN)
        admin = client.get("/api/v1/system/status")

    assert unauthenticated.status_code == 401
    assert analyst.status_code == 403
    assert analyst.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"
    assert admin.status_code == 200
    assert admin.json()["database"]["label"] == "SQLite Development Fallback"
    assert "database_url" not in admin.text.casefold()
