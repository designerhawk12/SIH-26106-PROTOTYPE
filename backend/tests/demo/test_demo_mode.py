"""Tests for explicit, synthetic-only optional-provider demo fallback."""

from __future__ import annotations

import asyncio
from hashlib import sha256
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.core import Settings
from backend.app.db import create_database_engine
from backend.app.schemas import EnrichmentStatus, GeoLocationStatus
from backend.app.services.geolocation import (
    DEMO_GEOLOCATION_PROVIDER,
    DemoInfrastructureGeoProvider,
)
from backend.app.services.orchestrator.factory import (
    DEMO_MODE_WARNING,
    build_default_analysis_orchestrator,
)
from backend.app.services.threat_intel import (
    DEMO_THREAT_INTEL_PROVIDER,
    DemoThreatIntelProvider,
)
from backend.main import create_app
from backend.tests.auth_helpers import AUTH_HEADERS, FakeIdentityVerifier

FIXTURES = Path(__file__).parents[3] / "fixtures" / "emails"


def _fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_demo_mode_defaults_false_and_requires_explicit_boolean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEMO_MODE", raising=False)
    assert Settings.from_environment().demo_mode is False

    monkeypatch.setenv("DEMO_MODE", "true")
    assert Settings.from_environment().demo_mode is True

    monkeypatch.setenv("DEMO_MODE", "false")
    assert Settings.from_environment().demo_mode is False

    monkeypatch.setenv("DEMO_MODE", "enabled")
    with pytest.raises(ValueError, match="DEMO_MODE"):
        Settings.from_environment()


def test_demo_mode_false_keeps_real_core_and_does_not_add_demo_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ABUSEIPDB_API_KEY", raising=False)
    monkeypatch.delenv("VIRUSTOTAL_API_KEY", raising=False)
    raw_email = _fixture("08_prompt_injection.eml")

    analysis = asyncio.run(
        build_default_analysis_orchestrator(Settings(demo_mode=False)).analyze(
            raw_email,
            original_filename="08_prompt_injection.eml",
        )
    )

    assert analysis.parsed_email is not None
    assert analysis.parsed_email.original_sha256 == sha256(raw_email).hexdigest()
    assert analysis.detection is not None
    assert analysis.detection.model_name == "deterministic_rules"
    assert analysis.risk is not None
    assert DEMO_MODE_WARNING not in analysis.warnings
    assert analysis.threat_intel is not None
    assert all(
        finding.provider != DEMO_THREAT_INTEL_PROVIDER
        for finding in analysis.threat_intel.findings
    )
    assert all(
        location.provider != DEMO_GEOLOCATION_PROVIDER
        for location in analysis.geolocations
    )


def test_demo_mode_true_uses_labelled_synthetic_optional_enrichment_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def network_must_not_run(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("demo mode must not make live provider requests")

    monkeypatch.setattr(httpx.AsyncClient, "get", network_must_not_run)
    raw_email = _fixture("02_phishing.eml")
    orchestrator = build_default_analysis_orchestrator(Settings(demo_mode=True))

    first = asyncio.run(
        orchestrator.analyze(raw_email, original_filename="02_phishing.eml")
    )
    second = asyncio.run(
        orchestrator.analyze(raw_email, original_filename="02_phishing.eml")
    )

    assert first.status.value == "PARTIAL"
    assert DEMO_MODE_WARNING in first.warnings
    assert first.parsed_email is not None
    assert first.parsed_email.original_sha256 == sha256(raw_email).hexdigest()
    assert first.detection is not None
    assert first.detection.model_name == "deterministic_rules"
    assert first.risk is not None
    assert second.risk is not None
    assert first.risk.score == second.risk.score
    assert first.risk.reasons == second.risk.reasons

    assert first.threat_intel is not None
    assert first.threat_intel.findings
    assert all(
        finding.provider == DEMO_THREAT_INTEL_PROVIDER
        for finding in first.threat_intel.findings
    )
    assert all(
        "Synthetic demo fallback" in (finding.details or "")
        for finding in first.threat_intel.findings
    )
    assert first.geolocations
    assert all(
        location.provider == DEMO_GEOLOCATION_PROVIDER
        for location in first.geolocations
    )
    assert all(
        location.observed_infrastructure_only for location in first.geolocations
    )


def test_demo_provider_failure_does_not_prevent_real_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_threat_lookup(
        _self: DemoThreatIntelProvider, _indicator: object
    ) -> object:
        raise RuntimeError("controlled demo provider failure")

    async def fail_geolocation(
        _self: DemoInfrastructureGeoProvider, _ip_address: str
    ) -> object:
        raise RuntimeError("controlled demo provider failure")

    monkeypatch.setattr(DemoThreatIntelProvider, "lookup", fail_threat_lookup)
    monkeypatch.setattr(DemoInfrastructureGeoProvider, "locate", fail_geolocation)
    raw_email = _fixture("03_bec.eml")

    analysis = asyncio.run(
        build_default_analysis_orchestrator(Settings(demo_mode=True)).analyze(raw_email)
    )

    assert analysis.parsed_email is not None
    assert analysis.parsed_email.original_sha256 == sha256(raw_email).hexdigest()
    assert analysis.detection is not None
    assert analysis.risk is not None
    assert analysis.status.value == "PARTIAL"
    assert analysis.threat_intel is not None
    assert analysis.threat_intel.status is EnrichmentStatus.UNAVAILABLE
    assert analysis.threat_intel.provider_errors
    assert analysis.geolocations
    assert all(
        result.status is GeoLocationStatus.PROVIDER_ERROR
        for result in analysis.geolocations
    )


def test_api_uses_explicit_demo_setting_and_persists_labelled_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def network_must_not_run(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("demo mode must not make live provider requests")

    monkeypatch.setattr(httpx.AsyncClient, "get", network_must_not_run)
    raw_email = _fixture("02_phishing.eml")
    app = create_app(
        settings=Settings(demo_mode=True, database_url="sqlite://"),
        identity_verifier=FakeIdentityVerifier(),
        database_engine=create_database_engine("sqlite://"),
    )

    with TestClient(app, headers=AUTH_HEADERS) as client:
        response = client.post(
            "/api/v1/cases/analyze",
            files={"file": ("02_phishing.eml", raw_email, "message/rfc822")},
        )
        assert response.status_code == 201
        submitted = response.json()["analysis"]
        persisted = client.get(f"/api/v1/cases/{submitted['case_id']}")

    assert persisted.status_code == 200
    assert persisted.json() == submitted
    assert submitted["status"] == "PARTIAL"
    assert DEMO_MODE_WARNING in submitted["warnings"]
    assert (
        submitted["parsed_email"]["original_sha256"]
        == sha256(raw_email).hexdigest()
    )
    assert submitted["detection"]["model_name"] == "deterministic_rules"
    assert submitted["risk"] is not None
    assert all(
        finding["provider"] == DEMO_THREAT_INTEL_PROVIDER
        for finding in submitted["threat_intel"]["findings"]
    )
    assert all(
        location["provider"] == DEMO_GEOLOCATION_PROVIDER
        for location in submitted["geolocations"]
    )
