"""API contract tests using injected mock feature services."""

from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient

from backend.app.core import Settings
from backend.app.db import create_database_engine
from backend.app.schemas import (
    DetectionResult,
    EnrichmentStatus,
    ExtractedIOC,
    GeoLocationResult,
    GeoLocationStatus,
    IOCSource,
    IOCType,
    ParsedEmail,
    RiskLevel,
    RiskReason,
    RiskResult,
    ThreatIntelResult,
)
from backend.app.services.orchestrator import AnalysisPipelineOrchestrator
from backend.main import create_app
from backend.tests.auth_helpers import AUTH_HEADERS, FakeIdentityVerifier


class MockEmailForensicsService:
    def parse(self, raw_email: bytes, *, original_filename: str | None = None) -> ParsedEmail:
        return ParsedEmail(
            original_sha256=sha256(raw_email).hexdigest(),
            subject="Mock subject",
            originating_public_ips=("203.0.113.42",),
            iocs=(
                ExtractedIOC(
                    type=IOCType.DOMAIN,
                    value="example.test",
                    normalized_value="example.test",
                    source=IOCSource.BODY_TEXT,
                ),
            ),
        )


class MockThreatDetectionService:
    async def detect(self, parsed_email: ParsedEmail) -> DetectionResult:
        return DetectionResult(summary=f"Analyzed {parsed_email.subject}")


class MockThreatIntelService:
    def __init__(self, *, fail: bool = False) -> None:
        self._fail = fail

    async def enrich(self, indicators: Sequence[ExtractedIOC]) -> ThreatIntelResult:
        if self._fail:
            raise RuntimeError("mock provider failure")
        return ThreatIntelResult(
            status=EnrichmentStatus.COMPLETE,
            requested_indicators=tuple(indicators),
        )


class MockGeoLocationService:
    async def locate_public_ips(
        self, ip_addresses: Sequence[str]
    ) -> tuple[GeoLocationResult, ...]:
        return tuple(
            GeoLocationResult(
                ip_address=ip_address,
                status=GeoLocationStatus.UNKNOWN,
            )
            for ip_address in ip_addresses
        )


class MockRiskService:
    def score(
        self,
        *,
        parsed_email: ParsedEmail,
        detection: DetectionResult,
        threat_intel: ThreatIntelResult,
        geolocations: Sequence[GeoLocationResult],
    ) -> RiskResult:
        return RiskResult(
            score=10,
            severity=RiskLevel.LOW,
            reasons=(
                RiskReason(
                    code="MOCK_SIGNAL",
                    description="Mock risk contribution.",
                    points=10,
                ),
            ),
            formula_version="mock-v1",
        )


class MockReportingService:
    async def render_pdf(self, analysis: object) -> bytes:
        return b"%PDF-1.4\nmock report\n%%EOF"


def build_test_app(*, max_upload_bytes: int = 1024, threat_failure: bool = False):
    settings = Settings(
        app_version="test",
        database_url="sqlite://",
        max_upload_bytes=max_upload_bytes,
        allowed_origins=("http://testserver",),
    )
    pipeline = AnalysisPipelineOrchestrator(
        email_forensics=MockEmailForensicsService(),
        threat_detection=MockThreatDetectionService(),
        threat_intel=MockThreatIntelService(fail=threat_failure),
        geolocation=MockGeoLocationService(),
        risk=MockRiskService(),
    )
    return create_app(
        settings=settings,
        analysis_orchestrator=pipeline,
        reporting_service=MockReportingService(),
        identity_verifier=FakeIdentityVerifier(),
        database_engine=create_database_engine("sqlite://"),
    )


@pytest.fixture
def client() -> TestClient:
    with TestClient(build_test_app(), headers=AUTH_HEADERS) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "test"
    assert response.headers["X-Request-ID"]


def test_analyze_list_get_and_report(client: TestClient) -> None:
    response = client.post(
        "/api/v1/cases/analyze",
        files={"file": ("message.eml", b"From: sender@example.test\n\nHello")},
    )
    assert response.status_code == 201
    analysis = response.json()["analysis"]
    assert analysis["status"] == "COMPLETED"
    assert analysis["original_filename"] == "message.eml"
    case_id = analysis["case_id"]

    listing = client.get("/api/v1/cases")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["case_id"] == case_id
    assert listing.json()["items"][0]["risk_severity"] == "LOW"

    detail = client.get(f"/api/v1/cases/{case_id}")
    assert detail.status_code == 200
    assert detail.json()["parsed_email"]["subject"] == "Mock subject"

    report = client.get(f"/api/v1/cases/{case_id}/report")
    assert report.status_code == 200
    assert report.headers["content-type"] == "application/pdf"
    assert report.content.startswith(b"%PDF-1.4")


def test_provider_failure_returns_and_persists_partial_analysis() -> None:
    with TestClient(build_test_app(threat_failure=True), headers=AUTH_HEADERS) as client:
        response = client.post(
            "/api/v1/cases/analyze",
            files={"file": ("message.eml", b"From: sender@example.test\n\nHello")},
        )
        assert response.status_code == 201
        analysis = response.json()["analysis"]
        assert analysis["status"] == "PARTIAL"
        assert analysis["threat_intel"]["status"] == "UNAVAILABLE"
        assert analysis["threat_intel"]["unknown_indicators"]
        case_id = analysis["case_id"]
        assert client.get(f"/api/v1/cases/{case_id}").json()["status"] == "PARTIAL"


@pytest.mark.parametrize(
    ("filename", "content", "expected_status", "expected_code"),
    [
        (" ", b"content", 400, "MISSING_FILENAME"),
        ("message.txt", b"content", 415, "UNSUPPORTED_FILE_TYPE"),
        ("message.eml", b"", 400, "EMPTY_FILE"),
    ],
)
def test_upload_validation(
    client: TestClient,
    filename: str,
    content: bytes,
    expected_status: int,
    expected_code: str,
) -> None:
    response = client.post(
        "/api/v1/cases/analyze",
        files={"file": (filename, content)},
    )
    assert response.status_code == expected_status
    assert response.json()["error"]["code"] == expected_code
    assert response.json()["request_id"]


def test_upload_size_limit() -> None:
    with TestClient(build_test_app(max_upload_bytes=3), headers=AUTH_HEADERS) as client:
        response = client.post(
            "/api/v1/cases/analyze",
            files={"file": ("message.eml", b"1234")},
        )
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "UPLOAD_TOO_LARGE"


def test_missing_file_is_structured_validation_error(client: TestClient) -> None:
    response = client.post("/api/v1/cases/analyze")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["field"] == "file"


def test_case_not_found_is_structured(client: TestClient) -> None:
    response = client.get("/api/v1/cases/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CASE_NOT_FOUND"

