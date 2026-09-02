"""End-to-end orchestration tests using real deterministic feature services."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path

import pytest

from backend.app.schemas import (
    AnalysisStatus,
    DetectionCategory,
    EnrichmentStatus,
    ExtractedIOC,
    GeoLocationResult,
    GeoLocationStatus,
    ParsedEmail,
    ThreatIntelResult,
)
from backend.app.services.detection import DeterministicDetectionService
from backend.app.services.email_forensics import EmailForensicsParser
from backend.app.services.geolocation import ObservedInfrastructureGeoService
from backend.app.services.orchestrator import (
    AnalysisPipelineOrchestrator,
    EmailAnalysisError,
)
from backend.app.services.risk import DeterministicRiskEngine


FIXTURES = Path(__file__).parents[3] / "fixtures" / "emails"


class ControlledThreatIntel:
    def __init__(self, status: EnrichmentStatus = EnrichmentStatus.COMPLETE) -> None:
        self._status = status

    async def enrich(self, indicators: Sequence[ExtractedIOC]) -> ThreatIntelResult:
        requested = tuple(indicators)
        unavailable = self._status is not EnrichmentStatus.COMPLETE
        return ThreatIntelResult(
            status=self._status,
            requested_indicators=requested,
            unknown_indicators=requested if unavailable else (),
            provider_errors=("Test provider unavailable.",) if unavailable else (),
        )


class ControlledGeoLocation:
    def __init__(self, status: GeoLocationStatus = GeoLocationStatus.FOUND) -> None:
        self._status = status

    async def locate_public_ips(
        self, ip_addresses: Sequence[str]
    ) -> tuple[GeoLocationResult, ...]:
        return tuple(
            GeoLocationResult(
                ip_address=ip_address,
                status=self._status,
                provider="test-provider",
            )
            for ip_address in ip_addresses
        )


def pipeline(
    *,
    threat_status: EnrichmentStatus = EnrichmentStatus.COMPLETE,
    geo_status: GeoLocationStatus = GeoLocationStatus.FOUND,
) -> AnalysisPipelineOrchestrator:
    return AnalysisPipelineOrchestrator(
        email_forensics=EmailForensicsParser(),
        threat_detection=DeterministicDetectionService(),
        threat_intel=ControlledThreatIntel(threat_status),
        geolocation=ControlledGeoLocation(geo_status),
        risk=DeterministicRiskEngine(),
    )


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def categories(analysis: object) -> set[DetectionCategory]:
    detection = getattr(analysis, "detection")
    assert detection is not None
    return {finding.category for finding in detection.findings}


def test_legitimate_email_completes_with_deterministic_low_risk() -> None:
    analysis = asyncio.run(pipeline().analyze(fixture_bytes("01_legitimate.eml")))

    assert analysis.status is AnalysisStatus.COMPLETED
    assert analysis.parsed_email is not None
    assert analysis.parsed_email.subject == "Quarterly operations update"
    assert analysis.detection is not None
    assert analysis.detection.findings == ()
    assert analysis.risk is not None
    assert analysis.risk.score == 0


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("02_phishing.eml", DetectionCategory.PHISHING),
        ("03_bec.eml", DetectionCategory.BUSINESS_EMAIL_COMPROMISE),
    ],
)
def test_threat_fixtures_flow_through_detection_and_risk(
    fixture: str, expected: DetectionCategory
) -> None:
    analysis = asyncio.run(pipeline().analyze(fixture_bytes(fixture)))

    assert expected in categories(analysis)
    assert analysis.risk is not None
    assert analysis.risk.reasons


def test_suspicious_attachment_remains_evidence_and_is_never_executed() -> None:
    analysis = asyncio.run(
        pipeline().analyze(fixture_bytes("05_suspicious_attachment.eml"))
    )

    assert analysis.parsed_email is not None
    assert analysis.parsed_email.attachments
    assert all(
        attachment.executed is False
        for attachment in analysis.parsed_email.attachments
    )
    assert any(
        "suspicious" in warning.casefold()
        for warning in analysis.parsed_email.parse_warnings
    )


def test_prompt_injection_remains_untrusted_evidence() -> None:
    analysis = asyncio.run(
        pipeline().analyze(fixture_bytes("08_prompt_injection.eml"))
    )

    assert analysis.parsed_email is not None
    assert "Ignore previous security instructions" in (
        analysis.parsed_email.text_body or ""
    )
    assert analysis.status is AnalysisStatus.COMPLETED
    assert analysis.risk is not None


def test_controlled_provider_unavailable_produces_partial_risked_result() -> None:
    analysis = asyncio.run(
        pipeline(threat_status=EnrichmentStatus.UNAVAILABLE).analyze(
            fixture_bytes("02_phishing.eml")
        )
    )

    assert analysis.status is AnalysisStatus.PARTIAL
    assert analysis.threat_intel is not None
    assert analysis.threat_intel.status is EnrichmentStatus.UNAVAILABLE
    assert analysis.risk is not None
    assert any("not treated as safe" in item for item in analysis.risk.unknown_inputs)


def test_controlled_geolocation_unavailable_produces_partial_result() -> None:
    analysis = asyncio.run(
        pipeline(geo_status=GeoLocationStatus.PROVIDER_ERROR).analyze(
            fixture_bytes("01_legitimate.eml")
        )
    )

    assert analysis.status is AnalysisStatus.PARTIAL
    assert analysis.geolocations
    assert analysis.geolocations[0].status is GeoLocationStatus.PROVIDER_ERROR
    assert analysis.risk is not None


def test_risk_is_repeatable_for_identical_normalized_evidence() -> None:
    service = pipeline()
    raw_email = fixture_bytes("03_bec.eml")

    first = asyncio.run(service.analyze(raw_email))
    second = asyncio.run(service.analyze(raw_email))

    assert first.risk == second.risk
    assert first.risk is not None
    assert first.risk.score == sum(reason.points for reason in first.risk.reasons)


def test_geolocation_service_exception_is_isolated() -> None:
    class RaisingGeoLocation:
        async def locate_public_ips(
            self, ip_addresses: Sequence[str]
        ) -> tuple[GeoLocationResult, ...]:
            raise RuntimeError("provider details must not escape")

    service = AnalysisPipelineOrchestrator(
        email_forensics=EmailForensicsParser(),
        threat_detection=DeterministicDetectionService(),
        threat_intel=ControlledThreatIntel(),
        geolocation=RaisingGeoLocation(),
        risk=DeterministicRiskEngine(),
    )
    analysis = asyncio.run(service.analyze(fixture_bytes("01_legitimate.eml")))

    assert analysis.status is AnalysisStatus.PARTIAL
    assert analysis.risk is not None
    assert analysis.geolocations[0].status is GeoLocationStatus.PROVIDER_ERROR
    assert "provider details" not in " ".join(analysis.warnings)


def test_core_email_forensics_failure_is_cleanly_normalized() -> None:
    class RaisingForensics:
        def parse(
            self, raw_email: bytes, *, original_filename: str | None = None
        ) -> ParsedEmail:
            raise ValueError("hostile parser detail")

    service = AnalysisPipelineOrchestrator(
        email_forensics=RaisingForensics(),
        threat_detection=DeterministicDetectionService(),
        threat_intel=ControlledThreatIntel(),
        geolocation=ObservedInfrastructureGeoService(provider=None),
        risk=DeterministicRiskEngine(),
    )

    with pytest.raises(EmailAnalysisError, match="Email parsing failed") as caught:
        asyncio.run(service.analyze(b"not an email"))

    assert "hostile parser detail" not in str(caught.value)
