"""API-to-orchestrator persistence integration without live providers."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from backend.app.core import Settings
from backend.app.db import create_database_engine
from backend.app.schemas import (
    EnrichmentStatus,
    ExtractedIOC,
    GeoLocationResult,
    GeoLocationStatus,
    ThreatIntelResult,
)
from backend.app.services.detection import DeterministicDetectionService
from backend.app.services.email_forensics import EmailForensicsParser
from backend.app.services.orchestrator import AnalysisPipelineOrchestrator
from backend.app.services.risk import DeterministicRiskEngine
from backend.main import create_app

FIXTURES = Path(__file__).parents[3] / "fixtures" / "emails"


class ControlledThreatIntel:
    async def enrich(self, indicators: Sequence[ExtractedIOC]) -> ThreatIntelResult:
        return ThreatIntelResult(
            status=EnrichmentStatus.COMPLETE,
            requested_indicators=tuple(indicators),
        )


class ControlledGeoLocation:
    async def locate_public_ips(
        self, ip_addresses: Sequence[str]
    ) -> tuple[GeoLocationResult, ...]:
        return tuple(
            GeoLocationResult(
                ip_address=ip_address,
                status=GeoLocationStatus.FOUND,
                provider="test-provider",
            )
            for ip_address in ip_addresses
        )


def test_analyze_persists_and_api_retrieves_normalized_analysis() -> None:
    engine = create_database_engine("sqlite://")
    orchestrator = AnalysisPipelineOrchestrator(
        email_forensics=EmailForensicsParser(),
        threat_detection=DeterministicDetectionService(),
        threat_intel=ControlledThreatIntel(),
        geolocation=ControlledGeoLocation(),
        risk=DeterministicRiskEngine(),
    )
    app = create_app(
        settings=Settings(
            database_url="sqlite://", allowed_origins=("http://testserver",)
        ),
        analysis_orchestrator=orchestrator,
        database_engine=engine,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/cases/analyze",
            files={
                "file": (
                    "phishing.eml",
                    (FIXTURES / "02_phishing.eml").read_bytes(),
                    "message/rfc822",
                )
            },
        )
        assert response.status_code == 201
        submitted = response.json()["analysis"]

        detail = client.get(f"/api/v1/cases/{submitted['case_id']}")
        listing = client.get("/api/v1/cases")

        assert detail.status_code == 200
        assert detail.json() == submitted
        assert listing.status_code == 200
        assert listing.json()["total"] == 1
        assert listing.json()["items"][0]["case_id"] == submitted["case_id"]
        assert listing.json()["items"][0]["risk_score"] == submitted["risk"]["score"]


def test_default_api_dependency_composes_pipeline_without_provider_keys(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("ABUSEIPDB_API_KEY", raising=False)
    monkeypatch.delenv("VIRUSTOTAL_API_KEY", raising=False)
    engine = create_database_engine("sqlite://")
    app = create_app(
        settings=Settings(database_url="sqlite://"),
        database_engine=engine,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/cases/analyze",
            files={
                "file": (
                    "message.eml",
                    b"From: sender@example.test\nTo: analyst@example.org\n\nHello",
                    "message/rfc822",
                )
            },
        )

    assert response.status_code == 201
    assert response.json()["analysis"]["parsed_email"] is not None
    assert response.json()["analysis"]["status"] == "PARTIAL"
