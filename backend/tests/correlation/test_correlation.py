"""Regression tests for persisted, deterministic cross-case correlation."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.core import Settings
from backend.app.db import (
    SqlAlchemyCaseRepository,
    SqlAlchemyUserProfileRepository,
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from backend.app.schemas import (
    AnalysisStatus,
    AttachmentEvidence,
    EmailAnalysis,
    ExtractedIOC,
    GeoLocationResult,
    GeoLocationStatus,
    IOCSource,
    IOCType,
    MailboxAddress,
    ParsedEmail,
    RiskLevel,
    RiskReason,
    RiskResult,
    UserRole,
)
from backend.app.services.auth import AuthenticatedIdentity
from backend.app.services.orchestrator.correlation import correlate_case
from backend.main import create_app
from backend.tests.auth_helpers import AUTH_HEADERS, FakeIdentityVerifier, TEST_USER_ID

NOW = datetime(2026, 9, 8, 10, 0, tzinfo=timezone.utc)
HASH = "a" * 64


def _ioc(ioc_type: IOCType, value: str) -> ExtractedIOC:
    return ExtractedIOC(
        type=ioc_type,
        value=value,
        normalized_value=value,
        source=IOCSource.BODY_TEXT,
    )


def _analysis(
    number: int,
    *,
    sender: str = "sender@example.test",
    reply_to: str | None = None,
    subject: str = "Quarterly update",
    iocs: tuple[ExtractedIOC, ...] = (),
    origin_ips: tuple[str, ...] = (),
    attachment_hash: str | None = None,
    asn: str | None = None,
) -> EmailAnalysis:
    attachments = (
        (
            AttachmentEvidence(
                attachment_id=f"attachment-{number}",
                filename="invoice.txt",
                content_type="text/plain",
                size_bytes=12,
                sha256=attachment_hash,
            ),
        )
        if attachment_hash
        else ()
    )
    geolocations = (
        (
            GeoLocationResult(
                ip_address="8.8.8.8",
                status=GeoLocationStatus.FOUND,
                asn=asn,
            ),
        )
        if asn
        else ()
    )
    return EmailAnalysis(
        case_id=UUID(f"00000000-0000-4000-8000-{number:012d}"),
        status=AnalysisStatus.COMPLETED,
        created_at=NOW,
        parsed_email=ParsedEmail(
            original_sha256=f"{number:064x}",
            subject=subject,
            sender=MailboxAddress(address=sender),
            reply_to=(MailboxAddress(address=reply_to),) if reply_to else (),
            iocs=iocs,
            originating_public_ips=origin_ips,
            attachments=attachments,
        ),
        geolocations=geolocations,
        risk=RiskResult(
            score=50,
            severity=RiskLevel.HIGH,
            reasons=(RiskReason(code="TEST", points=50, description="Test reason."),),
            formula_version="1.0",
        ),
    )


def test_shared_domain_ip_url_hash_and_sender_are_explainable() -> None:
    target = _analysis(
        1,
        sender="billing@evil.test",
        reply_to="verify@evil.test",
        subject="Re: Action required",
        iocs=(
            _ioc(IOCType.DOMAIN, "evil.test"),
            _ioc(IOCType.URL, "https://evil.test/login"),
        ),
        origin_ips=("8.8.8.8",),
        attachment_hash=HASH,
        asn="AS64500",
    )
    candidate = _analysis(
        2,
        sender="billing@evil.test",
        reply_to="verify@evil.test",
        subject="Fwd: Action required",
        iocs=(
            _ioc(IOCType.DOMAIN, "evil.test"),
            _ioc(IOCType.URL, "https://evil.test/login"),
        ),
        origin_ips=("8.8.8.8",),
        attachment_hash=HASH,
        asn="AS64500",
    )

    result = correlate_case(target, (target, candidate))

    assert result.total == 1
    related = result.items[0]
    assert related.correlation_strength.value == "HIGH"
    assert related.shared_indicator_count == 10
    assert {item.indicator_type.value for item in related.shared_indicators} >= {
        "SENDER_EMAIL",
        "REPLY_TO",
        "IP_ADDRESS",
        "DOMAIN",
        "URL",
        "ATTACHMENT_SHA256",
        "ASN",
        "NORMALIZED_SUBJECT",
    }
    assert any("attachment SHA-256" in reason for reason in related.relationship_reasons)


def test_shared_public_routing_infrastructure_is_low_strength_not_attribution() -> None:
    target = _analysis(
        1,
        sender="one@legitimate.test",
        subject="Routine operations update",
        origin_ips=("8.8.8.8",),
    )
    candidate = _analysis(
        2,
        sender="two@another.test",
        subject="Unrelated monthly notice",
        origin_ips=("8.8.8.8",),
    )

    related = correlate_case(target, (target, candidate)).items[0]

    assert related.correlation_strength.value == "LOW"
    assert related.shared_indicator_count == 1
    assert "does not establish a shared sender or campaign" in related.relationship_reasons[-1]


def test_sender_address_and_its_derived_domain_are_not_overcounted() -> None:
    target = _analysis(
        1,
        sender="billing@evil.test",
        iocs=(_ioc(IOCType.DOMAIN, "evil.test"),),
    )
    candidate = _analysis(
        2,
        sender="billing@evil.test",
        iocs=(_ioc(IOCType.DOMAIN, "evil.test"),),
    )

    related = correlate_case(target, (target, candidate)).items[0]

    assert related.correlation_strength.value == "MEDIUM"


def test_no_shared_forensic_indicators_returns_no_relationship() -> None:
    target = _analysis(1, sender="one@first.test", subject="First case")
    candidate = _analysis(2, sender="two@second.test", subject="Second case")

    assert correlate_case(target, (target, candidate)).items == ()


def test_correlation_is_repeatable_and_paginates_deterministically() -> None:
    target = _analysis(1, iocs=(_ioc(IOCType.DOMAIN, "shared.test"),))
    candidates = (
        target,
        _analysis(3, iocs=(_ioc(IOCType.DOMAIN, "shared.test"),)),
        _analysis(2, iocs=(_ioc(IOCType.DOMAIN, "shared.test"),)),
    )

    first = correlate_case(target, candidates)
    second = correlate_case(target, candidates)
    page = correlate_case(target, candidates, limit=1, offset=1)

    assert first.model_dump() == second.model_dump()
    assert first.total == 2
    assert len(page.items) == 1
    assert page.items[0].case_id == first.items[1].case_id


def _client_with_cases(
    *analyses: EmailAnalysis,
    role: UserRole = UserRole.SENIOR_ANALYST,
) -> TestClient:
    engine = create_database_engine("sqlite://")
    initialize_database(engine)
    factory = create_session_factory(engine)
    identity = AuthenticatedIdentity(
        user_id=TEST_USER_ID,
        email="analyst@example.test",
        user_metadata={"display_name": "Senior Test Analyst"},
    )
    with factory() as session:
        cases = SqlAlchemyCaseRepository(session)
        for analysis in analyses:
            cases.create(analysis)
        profiles = SqlAlchemyUserProfileRepository(session)
        profiles.get_or_create(identity)
        profiles.update_role(TEST_USER_ID, role)
    app = create_app(
        settings=Settings(database_url="sqlite://"),
        database_engine=engine,
        identity_verifier=FakeIdentityVerifier(),
    )
    return TestClient(app, headers=AUTH_HEADERS)


def test_related_endpoint_requires_auth_and_returns_persisted_results(monkeypatch) -> None:
    def pipeline_must_not_be_built(*_args, **_kwargs):
        raise AssertionError("Correlation retrieval must not construct providers")

    monkeypatch.setattr(
        "backend.app.api.dependencies.build_default_analysis_orchestrator",
        pipeline_must_not_be_built,
    )
    target = _analysis(
        1,
        sender="first@one.test",
        subject="First notice",
        iocs=(_ioc(IOCType.URL, "https://shared.test/login"),),
    )
    candidate = _analysis(
        2,
        sender="second@two.test",
        subject="Second notice",
        iocs=(_ioc(IOCType.URL, "https://shared.test/login"),),
    )
    with _client_with_cases(target, candidate) as client:
        client.headers["Authorization"] = ""
        unauthenticated = client.get(f"/api/v1/cases/{target.case_id}/related")
        client.headers.update(AUTH_HEADERS)
        response = client.get(f"/api/v1/cases/{target.case_id}/related")

    assert unauthenticated.status_code == 401
    assert response.status_code == 200
    assert response.json()["items"][0]["case_id"] == str(candidate.case_id)
    assert response.json()["items"][0]["correlation_strength"] == "MEDIUM"


def test_related_endpoint_handles_missing_case() -> None:
    target = _analysis(1)
    with _client_with_cases(target) as client:
        response = client.get("/api/v1/cases/00000000-0000-4000-8000-000000009999/related")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CASE_NOT_FOUND"


def test_related_endpoint_requires_campaign_access_permission() -> None:
    target = _analysis(1, iocs=(_ioc(IOCType.DOMAIN, "shared.test"),))
    candidate = _analysis(2, iocs=(_ioc(IOCType.DOMAIN, "shared.test"),))
    with _client_with_cases(target, candidate, role=UserRole.ANALYST) as client:
        response = client.get(f"/api/v1/cases/{target.case_id}/related")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INSUFFICIENT_PERMISSION"
