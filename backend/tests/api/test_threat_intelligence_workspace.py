"""Persisted threat-intelligence workspace API tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.core import Settings
from backend.app.db import (
    SqlAlchemyCaseRepository,
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from backend.app.schemas import (
    AnalysisStatus,
    AttachmentEvidence,
    EmailAnalysis,
    EnrichmentStatus,
    ExtractedIOC,
    GeoLocationResult,
    GeoLocationStatus,
    IOCSource,
    IOCType,
    ParsedEmail,
    ReputationVerdict,
    ThreatFinding,
    ThreatIntelResult,
)
from backend.app.services.orchestrator.threat_workspace import (
    aggregate_persisted_threat_intelligence,
)
from backend.main import create_app
from backend.tests.auth_helpers import AUTH_HEADERS, FakeIdentityVerifier

NOW = datetime(2026, 9, 4, 10, 0, tzinfo=timezone.utc)
HASH = "a" * 64


def _ioc(ioc_type: IOCType, value: str) -> ExtractedIOC:
    return ExtractedIOC(
        type=ioc_type,
        value=value,
        normalized_value=value,
        source=IOCSource.BODY_TEXT,
    )


def _analysis(
    case_number: int,
    *,
    iocs: tuple[ExtractedIOC, ...] = (),
    findings: tuple[ThreatFinding, ...] = (),
    status: EnrichmentStatus = EnrichmentStatus.COMPLETE,
    errors: tuple[str, ...] = (),
    demo: bool = False,
    attachment: bool = False,
) -> EmailAnalysis:
    attachments = (
        (
            AttachmentEvidence(
                attachment_id="attachment-1",
                filename="invoice.pdf.exe",
                content_type="text/plain",
                size_bytes=4,
                sha256=HASH,
            ),
        )
        if attachment
        else ()
    )
    return EmailAnalysis(
        case_id=UUID(f"00000000-0000-4000-8000-{case_number:012d}"),
        status=(
            AnalysisStatus.PARTIAL
            if status is not EnrichmentStatus.COMPLETE
            else AnalysisStatus.COMPLETED
        ),
        original_filename=f"case-{case_number}.eml",
        created_at=NOW,
        parsed_email=ParsedEmail(
            original_sha256=f"{case_number:x}" * 64,
            subject=f"Case {case_number}",
            iocs=iocs,
            attachments=attachments,
        ),
        threat_intel=ThreatIntelResult(
            status=status,
            requested_indicators=iocs,
            findings=findings,
            unknown_indicators=tuple(ioc for ioc in iocs if not findings),
            provider_errors=errors,
        ),
        geolocations=(
            GeoLocationResult(
                ip_address="8.8.8.8",
                status=GeoLocationStatus.FOUND,
                provider=(
                    "DEMO-SYNTHETIC (not live verified)" if demo else "ipwho.is"
                ),
            ),
        ),
        warnings=("Demo Mode is explicitly enabled." if demo else "",) if demo else (),
    )


def test_multiple_cases_aggregate_persisted_iocs_without_losing_semantics() -> None:
    ip = _ioc(IOCType.IP_ADDRESS, "8.8.8.8")
    domain = _ioc(IOCType.DOMAIN, "example.test")
    url = _ioc(IOCType.URL, "https://example.test/login")
    attachment_hash = _ioc(IOCType.ATTACHMENT_SHA256, HASH)
    analyses = (
        _analysis(
            1,
            iocs=(ip, domain, url),
            findings=(
                ThreatFinding(
                    indicator_type=IOCType.IP_ADDRESS,
                    indicator="8.8.8.8",
                    provider="AbuseIPDB",
                    verdict=ReputationVerdict.MALICIOUS,
                    confidence=0.9,
                    categories=("abuse",),
                    details="High provider abuse confidence.",
                ),
                ThreatFinding(
                    indicator_type=IOCType.DOMAIN,
                    indicator="example.test",
                    provider="VirusTotal",
                    verdict=ReputationVerdict.BENIGN,
                ),
            ),
        ),
        _analysis(2, iocs=(ip,), status=EnrichmentStatus.UNKNOWN),
        _analysis(
            3,
            iocs=(attachment_hash,),
            status=EnrichmentStatus.UNAVAILABLE,
            errors=("VirusTotal: provider unavailable.",),
            attachment=True,
        ),
    )

    workspace = aggregate_persisted_threat_intelligence(analyses)
    by_value = {record.value: record for record in workspace.indicators}

    assert workspace.cases_scanned == 3
    assert workspace.summary.total_observed_iocs == 4
    assert workspace.summary.suspicious_or_malicious == 1
    assert workspace.summary.benign == 1
    assert workspace.summary.unknown == 1
    assert workspace.summary.unavailable == 1
    assert len(by_value["8.8.8.8"].associated_cases) == 2
    assert by_value[HASH].status.value == "UNAVAILABLE"
    assert by_value[HASH].filename == "invoice.pdf.exe"
    assert by_value["https://example.test/login"].status.value == "UNKNOWN"


def test_demo_intelligence_is_labelled_without_live_provider_attribution() -> None:
    domain = _ioc(IOCType.DOMAIN, "secure-login.example")
    workspace = aggregate_persisted_threat_intelligence(
        (
            _analysis(
                4,
                iocs=(domain,),
                findings=(
                    ThreatFinding(
                        indicator_type=IOCType.DOMAIN,
                        indicator=domain.normalized_value,
                        provider="DEMO-SYNTHETIC (not live verified)",
                        verdict=ReputationVerdict.SUSPICIOUS,
                    ),
                ),
                demo=True,
            ),
        )
    )

    record = workspace.indicators[0]
    assert record.demo is True
    assert record.providers == ("DEMO-SYNTHETIC (not live verified)",)
    demo_provider = next(provider for provider in workspace.providers if provider.demo)
    assert demo_provider.status.value == "AVAILABLE"
    live_providers = {
        provider.name: provider.status.value
        for provider in workspace.providers
        if provider.name in {"AbuseIPDB", "VirusTotal"}
    }
    assert live_providers == {"AbuseIPDB": "UNKNOWN", "VirusTotal": "UNKNOWN"}


def test_zero_ioc_workspace_has_explicit_empty_counts() -> None:
    workspace = aggregate_persisted_threat_intelligence(())
    assert workspace.summary.total_observed_iocs == 0
    assert workspace.indicators == ()
    assert all(provider.status.value == "UNKNOWN" for provider in workspace.providers)


def test_completed_not_found_lookup_remains_unknown_not_benign() -> None:
    domain = _ioc(IOCType.DOMAIN, "not-found.example")
    workspace = aggregate_persisted_threat_intelligence(
        (_analysis(6, iocs=(domain,), status=EnrichmentStatus.COMPLETE),)
    )

    assert workspace.indicators[0].status.value == "UNKNOWN"
    assert workspace.summary.unknown == 1
    assert workspace.summary.benign == 0
    virus_total = next(
        provider for provider in workspace.providers if provider.name == "VirusTotal"
    )
    assert virus_total.status.value == "AVAILABLE"


def test_read_endpoint_uses_persistence_and_makes_no_provider_calls(
    monkeypatch,
) -> None:
    def provider_pipeline_must_not_be_built(*_args, **_kwargs):
        raise AssertionError(
            "Viewing persisted intelligence must not construct providers"
        )

    monkeypatch.setattr(
        "backend.app.api.dependencies.build_default_analysis_orchestrator",
        provider_pipeline_must_not_be_built,
    )
    engine = create_database_engine("sqlite://")
    initialize_database(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        SqlAlchemyCaseRepository(session).create(
            _analysis(5, iocs=(_ioc(IOCType.DOMAIN, "persisted.test"),))
        )
    app = create_app(
        settings=Settings(database_url="sqlite://"),
        database_engine=engine,
        identity_verifier=FakeIdentityVerifier(),
    )
    with TestClient(app, headers=AUTH_HEADERS) as client:
        response = client.get("/api/v1/threat-intelligence")

    assert response.status_code == 200
    assert response.json()["summary"]["total_observed_iocs"] == 1
    assert response.json()["indicators"][0]["value"] == "persisted.test"
