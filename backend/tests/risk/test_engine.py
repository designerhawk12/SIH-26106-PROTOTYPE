"""Offline tests for deterministic Layer 5 risk scoring."""

from __future__ import annotations

from hashlib import sha256

import pytest

from backend.app.schemas import (
    AuthenticationResults,
    AuthenticationVerdict,
    DetectionCategory,
    DetectionFinding,
    DetectionResult,
    EnrichmentStatus,
    ExtractedIOC,
    IOCSource,
    IOCType,
    MailboxAddress,
    ParsedEmail,
    ReputationVerdict,
    RiskLevel,
    RiskResult,
    Severity,
    ThreatFinding,
    ThreatIntelResult,
)
from backend.app.services.risk import DeterministicRiskEngine, WEIGHTS, calculate_risk


def parsed_email(
    *,
    authentication: AuthenticationResults | None = None,
    reply_mismatch: bool = False,
) -> ParsedEmail:
    return ParsedEmail(
        original_sha256=sha256(b"risk-test").hexdigest(),
        sender=MailboxAddress(display_name="Finance", address="finance@example.org"),
        reply_to=(
            MailboxAddress(
                address="reply@external.test" if reply_mismatch else "reply@example.org"
            ),
        ),
        authentication=authentication
        or AuthenticationResults(
            spf=AuthenticationVerdict.PASS,
            dkim=AuthenticationVerdict.PASS,
            dmarc=AuthenticationVerdict.PASS,
        ),
    )


def detection_finding(
    category: DetectionCategory,
    *,
    title: str | None = None,
    evidence: tuple[str, ...] = ("test evidence",),
) -> DetectionFinding:
    return DetectionFinding(
        finding_id=f"test-{category.value.lower()}",
        category=category,
        severity=Severity.HIGH,
        confidence=1.0,
        title=title or category.value,
        explanation="Deterministic test evidence.",
        evidence=evidence,
        detector="test-rules:1",
    )


def threat_finding(
    indicator_type: IOCType,
    verdict: ReputationVerdict,
) -> ThreatFinding:
    values = {
        IOCType.URL: "https://example.test/login",
        IOCType.DOMAIN: "example.test",
        IOCType.IP_ADDRESS: "203.0.113.20",
        IOCType.ATTACHMENT_SHA256: "a" * 64,
    }
    return ThreatFinding(
        indicator_type=indicator_type,
        indicator=values[indicator_type],
        provider="TestProvider",
        verdict=verdict,
    )


def score(
    *,
    parsed: ParsedEmail | None = None,
    categories: tuple[DetectionCategory, ...] = (),
    display_impersonation: bool = False,
    threats: tuple[ThreatFinding, ...] = (),
    threat_status: EnrichmentStatus = EnrichmentStatus.COMPLETE,
) -> RiskResult:
    findings = [detection_finding(category) for category in categories]
    if display_impersonation:
        findings.append(
            detection_finding(
                DetectionCategory.IMPERSONATION,
                title="Display-name impersonation",
                evidence=("Sender display name: Chief Executive Officer",),
            )
        )
    return calculate_risk(
        parsed_email=parsed or parsed_email(),
        detection=DetectionResult(findings=tuple(findings)),
        threat_intel=ThreatIntelResult(status=threat_status, findings=threats),
    )


def reason_points(result: RiskResult) -> dict[str, int]:
    return {reason.code: reason.points for reason in result.reasons}


def test_zero_score_benign_case_is_low() -> None:
    result = score()

    assert result.score == 0
    assert result.severity is RiskLevel.LOW
    assert result.reasons == ()
    assert result.unknown_inputs == ()


@pytest.mark.parametrize(
    ("protocol", "code", "points"),
    (("spf", "spf_fail", 10), ("dkim", "dkim_fail", 8), ("dmarc", "dmarc_fail", 12)),
)
def test_individual_authentication_weights(protocol: str, code: str, points: int) -> None:
    verdicts = {
        "spf": AuthenticationVerdict.PASS,
        "dkim": AuthenticationVerdict.PASS,
        "dmarc": AuthenticationVerdict.PASS,
    }
    verdicts[protocol] = AuthenticationVerdict.FAIL
    parsed = parsed_email(authentication=AuthenticationResults(**verdicts))

    result = score(parsed=parsed)

    assert result.score == points
    assert reason_points(result) == {code: points}


@pytest.mark.parametrize(
    ("category", "code"),
    (
        (DetectionCategory.URGENCY, "urgency"),
        (DetectionCategory.CREDENTIAL_REQUEST, "credential_request"),
        (DetectionCategory.PAYMENT_REQUEST, "payment_request"),
        (DetectionCategory.SUSPICIOUS_CALL_TO_ACTION, "suspicious_cta"),
        (DetectionCategory.BUSINESS_EMAIL_COMPROMISE, "bec"),
    ),
)
def test_individual_detection_weights(category: DetectionCategory, code: str) -> None:
    result = score(categories=(category,))

    assert result.score == WEIGHTS[code]
    assert reason_points(result) == {code: WEIGHTS[code]}


def test_reply_to_and_display_name_are_separate_signals() -> None:
    reply_only = score(parsed=parsed_email(reply_mismatch=True))
    display_only = score(display_impersonation=True)

    assert reason_points(reply_only) == {"reply_to_domain_mismatch": 8}
    assert reason_points(display_only) == {"display_name_impersonation": 12}


@pytest.mark.parametrize(
    ("indicator_type", "verdict", "code"),
    (
        (IOCType.URL, ReputationVerdict.SUSPICIOUS, "suspicious_url"),
        (IOCType.DOMAIN, ReputationVerdict.MALICIOUS, "negative_domain_reputation"),
        (IOCType.IP_ADDRESS, ReputationVerdict.SUSPICIOUS, "negative_ip_reputation"),
        (
            IOCType.ATTACHMENT_SHA256,
            ReputationVerdict.MALICIOUS,
            "malicious_attachment_hash",
        ),
    ),
)
def test_individual_reputation_weights(
    indicator_type: IOCType, verdict: ReputationVerdict, code: str
) -> None:
    result = score(threats=(threat_finding(indicator_type, verdict),))

    assert result.score == WEIGHTS[code]
    assert reason_points(result) == {code: WEIGHTS[code]}


def test_suspicious_attachment_hash_does_not_receive_malicious_hash_weight() -> None:
    result = score(
        threats=(
            threat_finding(IOCType.ATTACHMENT_SHA256, ReputationVerdict.SUSPICIOUS),
        )
    )

    assert result.score == 0
    assert result.reasons == ()


@pytest.mark.parametrize(
    ("expected_score", "expected_severity", "categories", "auth_fail", "threats", "display"),
    (
        (
            24,
            RiskLevel.LOW,
            (DetectionCategory.CREDENTIAL_REQUEST,),
            None,
            (),
            True,
        ),
        (
            25,
            RiskLevel.MEDIUM,
            (DetectionCategory.PAYMENT_REQUEST, DetectionCategory.BUSINESS_EMAIL_COMPROMISE),
            None,
            (),
            False,
        ),
        (
            49,
            RiskLevel.MEDIUM,
            (DetectionCategory.BUSINESS_EMAIL_COMPROMISE, DetectionCategory.CREDENTIAL_REQUEST),
            "spf",
            (threat_finding(IOCType.DOMAIN, ReputationVerdict.MALICIOUS),),
            False,
        ),
        (
            50,
            RiskLevel.HIGH,
            (DetectionCategory.CREDENTIAL_REQUEST, DetectionCategory.PAYMENT_REQUEST),
            "dkim",
            (threat_finding(IOCType.ATTACHMENT_SHA256, ReputationVerdict.MALICIOUS),),
            False,
        ),
        (
            89,
            RiskLevel.HIGH,
            (
                DetectionCategory.BUSINESS_EMAIL_COMPROMISE,
                DetectionCategory.CREDENTIAL_REQUEST,
                DetectionCategory.PAYMENT_REQUEST,
                DetectionCategory.URGENCY,
                DetectionCategory.SUSPICIOUS_CALL_TO_ACTION,
            ),
            "dkim",
            (
                threat_finding(IOCType.ATTACHMENT_SHA256, ReputationVerdict.MALICIOUS),
                threat_finding(IOCType.DOMAIN, ReputationVerdict.MALICIOUS),
            ),
            False,
        ),
        (
            90,
            RiskLevel.CRITICAL,
            (
                DetectionCategory.CREDENTIAL_REQUEST,
                DetectionCategory.PAYMENT_REQUEST,
                DetectionCategory.URGENCY,
            ),
            "dkim",
            (
                threat_finding(IOCType.ATTACHMENT_SHA256, ReputationVerdict.MALICIOUS),
                threat_finding(IOCType.DOMAIN, ReputationVerdict.MALICIOUS),
                threat_finding(IOCType.IP_ADDRESS, ReputationVerdict.MALICIOUS),
                threat_finding(IOCType.URL, ReputationVerdict.MALICIOUS),
            ),
            False,
        ),
    ),
)
def test_exact_severity_threshold_boundaries(
    expected_score: int,
    expected_severity: RiskLevel,
    categories: tuple[DetectionCategory, ...],
    auth_fail: str | None,
    threats: tuple[ThreatFinding, ...],
    display: bool,
) -> None:
    verdicts = {
        "spf": AuthenticationVerdict.PASS,
        "dkim": AuthenticationVerdict.PASS,
        "dmarc": AuthenticationVerdict.PASS,
    }
    if auth_fail:
        verdicts[auth_fail] = AuthenticationVerdict.FAIL

    result = score(
        parsed=parsed_email(authentication=AuthenticationResults(**verdicts)),
        categories=categories,
        display_impersonation=display,
        threats=threats,
    )

    assert result.score == expected_score
    assert result.severity is expected_severity


def test_all_weights_combine_once_and_cap_at_100() -> None:
    parsed = parsed_email(
        authentication=AuthenticationResults(
            spf=AuthenticationVerdict.FAIL,
            dkim=AuthenticationVerdict.FAIL,
            dmarc=AuthenticationVerdict.FAIL,
        ),
        reply_mismatch=True,
    )
    categories = (
        DetectionCategory.URGENCY,
        DetectionCategory.CREDENTIAL_REQUEST,
        DetectionCategory.PAYMENT_REQUEST,
        DetectionCategory.SUSPICIOUS_CALL_TO_ACTION,
        DetectionCategory.BUSINESS_EMAIL_COMPROMISE,
    )
    threats = (
        threat_finding(IOCType.URL, ReputationVerdict.MALICIOUS),
        threat_finding(IOCType.DOMAIN, ReputationVerdict.MALICIOUS),
        threat_finding(IOCType.IP_ADDRESS, ReputationVerdict.MALICIOUS),
        threat_finding(IOCType.ATTACHMENT_SHA256, ReputationVerdict.MALICIOUS),
    )

    result = score(
        parsed=parsed,
        categories=categories,
        display_impersonation=True,
        threats=threats,
    )

    assert set(reason_points(result)) == set(WEIGHTS)
    assert sum(reason.points for reason in result.reasons) == sum(WEIGHTS.values()) == 153
    assert result.score == 100
    assert result.severity is RiskLevel.CRITICAL


def test_unknown_authentication_adds_no_points_and_is_not_called_safe() -> None:
    parsed = parsed_email(
        authentication=AuthenticationResults(
            spf=AuthenticationVerdict.UNKNOWN,
            dkim=AuthenticationVerdict.NONE,
            dmarc=AuthenticationVerdict.NEUTRAL,
        )
    )

    result = score(parsed=parsed)

    assert result.score == 0
    assert result.reasons == ()
    assert len(result.unknown_inputs) == 3
    assert all("not applied" in item for item in result.unknown_inputs)
    assert all("safe" not in item.casefold() for item in result.unknown_inputs)


def test_unavailable_threat_intelligence_adds_no_points_and_is_not_safe() -> None:
    indicator = ExtractedIOC(
        type=IOCType.DOMAIN,
        value="unknown.test",
        normalized_value="unknown.test",
        source=IOCSource.BODY_TEXT,
    )
    threat_intel = ThreatIntelResult(
        status=EnrichmentStatus.UNAVAILABLE,
        requested_indicators=(indicator,),
        unknown_indicators=(indicator,),
        provider_errors=("Provider unavailable.",),
    )

    result = calculate_risk(
        parsed_email=parsed_email(),
        detection=DetectionResult(),
        threat_intel=threat_intel,
    )

    assert result.score == 0
    assert result.reasons == ()
    assert any("UNAVAILABLE" in item for item in result.unknown_inputs)
    assert any("UNKNOWN/NOT_FOUND" in item for item in result.unknown_inputs)
    assert any("not treated as safe" in item for item in result.unknown_inputs)


def test_duplicate_findings_do_not_multiply_a_boolean_signal_weight() -> None:
    duplicate = detection_finding(DetectionCategory.URGENCY)
    result = calculate_risk(
        parsed_email=parsed_email(),
        detection=DetectionResult(
            findings=(
                duplicate,
                duplicate.model_copy(update={"finding_id": "second-urgency"}),
            )
        ),
        threat_intel=ThreatIntelResult(status=EnrichmentStatus.COMPLETE),
    )

    assert result.score == 6
    assert len(result.reasons) == 1
    assert len(result.reasons[0].evidence_refs) == 2


def test_risk_result_is_deterministically_repeatable_and_implements_interface() -> None:
    engine = DeterministicRiskEngine()
    inputs = {
        "parsed_email": parsed_email(reply_mismatch=True),
        "detection": DetectionResult(
            findings=(detection_finding(DetectionCategory.CREDENTIAL_REQUEST),)
        ),
        "threat_intel": ThreatIntelResult(status=EnrichmentStatus.COMPLETE),
        "geolocations": (),
    }

    first = engine.score(**inputs)
    second = engine.score(**inputs)

    assert first == second
    assert first.formula_version == "approved-screening-weights-v1"
    assert min(sum(reason.points for reason in first.reasons), 100) == first.score
