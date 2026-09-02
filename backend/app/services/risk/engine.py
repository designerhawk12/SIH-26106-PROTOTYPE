"""Deterministic, explainable Layer 5 risk scoring.

Every scored signal maps to one approved screening weight. Missing or
inconclusive evidence contributes no points and is recorded as unknown rather
than being interpreted as safe.
"""

from __future__ import annotations

from collections.abc import Sequence
from types import MappingProxyType

from ...schemas import (
    AuthenticationVerdict,
    DetectionCategory,
    DetectionFinding,
    DetectionResult,
    EnrichmentStatus,
    GeoLocationResult,
    IOCType,
    ParsedEmail,
    ReputationVerdict,
    RiskLevel,
    RiskReason,
    RiskResult,
    ThreatFinding,
    ThreatIntelResult,
)


FORMULA_VERSION = "approved-screening-weights-v1"
WEIGHTS = MappingProxyType(
    {
        "spf_fail": 10,
        "dkim_fail": 8,
        "dmarc_fail": 12,
        "reply_to_domain_mismatch": 8,
        "display_name_impersonation": 12,
        "urgency": 6,
        "credential_request": 12,
        "payment_request": 10,
        "suspicious_cta": 6,
        "bec": 15,
        "suspicious_url": 10,
        "negative_domain_reputation": 12,
        "negative_ip_reputation": 12,
        "malicious_attachment_hash": 20,
    }
)

_NEGATIVE_REPUTATION = frozenset(
    {ReputationVerdict.MALICIOUS, ReputationVerdict.SUSPICIOUS}
)


def _domain(address: str) -> str | None:
    if address.count("@") != 1:
        return None
    return address.rsplit("@", 1)[1].casefold().rstrip(".") or None


def _reply_to_mismatch(parsed_email: ParsedEmail) -> tuple[bool, tuple[str, ...]]:
    sender_domain = _domain(parsed_email.sender.address) if parsed_email.sender else None
    reply_domains = tuple(
        domain
        for mailbox in parsed_email.reply_to
        if (domain := _domain(mailbox.address)) is not None
    )
    if sender_domain and reply_domains and any(domain != sender_domain for domain in reply_domains):
        return True, (
            f"parsed_email.sender_domain:{sender_domain}",
            *(f"parsed_email.reply_to_domain:{domain}" for domain in reply_domains),
        )

    warning_refs = tuple(
        f"parsed_email.parse_warning:{index}"
        for index, warning in enumerate(parsed_email.parse_warnings)
        if "from and reply-to domains differ" in warning.casefold()
    )
    return bool(warning_refs), warning_refs


def _findings_for(
    detection: DetectionResult, category: DetectionCategory
) -> tuple[DetectionFinding, ...]:
    return tuple(finding for finding in detection.findings if finding.category is category)


def _finding_refs(findings: Sequence[DetectionFinding]) -> tuple[str, ...]:
    return tuple(f"detection:{finding.finding_id}" for finding in findings)


def _display_name_impersonation(
    detection: DetectionResult,
) -> tuple[bool, tuple[str, ...]]:
    findings = _findings_for(detection, DetectionCategory.IMPERSONATION)
    matching = tuple(
        finding
        for finding in findings
        if "display-name impersonation" in finding.title.casefold()
        or "display name impersonation" in finding.title.casefold()
        or any(evidence.casefold().startswith("sender display name:") for evidence in finding.evidence)
    )
    return bool(matching), _finding_refs(matching)


def _threat_refs(findings: Sequence[ThreatFinding]) -> tuple[str, ...]:
    return tuple(
        "threat_intel:"
        f"{finding.provider}:{finding.indicator_type.value}:{finding.indicator}:"
        f"{finding.verdict.value}"
        for finding in findings
    )


def _unknown_inputs(
    parsed_email: ParsedEmail, threat_intel: ThreatIntelResult
) -> tuple[str, ...]:
    unknowns: list[str] = []
    authentication = parsed_email.authentication
    for protocol, verdict in (
        ("SPF", authentication.spf),
        ("DKIM", authentication.dkim),
        ("DMARC", authentication.dmarc),
    ):
        if verdict not in {AuthenticationVerdict.PASS, AuthenticationVerdict.FAIL}:
            unknowns.append(
                f"{protocol} result is {verdict.value}; the approved FAIL weight was not applied."
            )

    if threat_intel.status is not EnrichmentStatus.COMPLETE:
        unknowns.append(
            f"Threat intelligence status is {threat_intel.status.value}; missing reputation "
            "data was not treated as safe and no unavailable-data weight was applied."
        )
    for indicator in threat_intel.unknown_indicators:
        unknowns.append(
            "Reputation data is UNKNOWN/NOT_FOUND for "
            f"{indicator.type.value}:{indicator.normalized_value}; no reputation weight was applied."
        )
    if threat_intel.provider_errors:
        unknowns.append(
            f"{len(threat_intel.provider_errors)} threat-intelligence provider error(s) occurred; "
            "affected reputation data was not treated as safe."
        )
    return tuple(dict.fromkeys(unknowns))


def _severity(score: int) -> RiskLevel:
    if score >= 90:
        return RiskLevel.CRITICAL
    if score >= 50:
        return RiskLevel.HIGH
    if score >= 25:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def calculate_risk(
    *,
    parsed_email: ParsedEmail,
    detection: DetectionResult,
    threat_intel: ThreatIntelResult,
    geolocations: Sequence[GeoLocationResult] = (),
) -> RiskResult:
    """Apply each approved boolean signal once and cap the result at 100."""

    del geolocations  # Infrastructure location is not an approved risk-weight input.
    reasons: list[RiskReason] = []

    def add_reason(
        code: str, description: str, evidence_refs: Sequence[str]
    ) -> None:
        reasons.append(
            RiskReason(
                code=code,
                description=description,
                points=WEIGHTS[code],
                evidence_refs=tuple(evidence_refs),
            )
        )

    authentication = parsed_email.authentication
    for protocol, verdict, code, description in (
        ("spf", authentication.spf, "spf_fail", "SPF authentication failed."),
        ("dkim", authentication.dkim, "dkim_fail", "DKIM authentication failed."),
        ("dmarc", authentication.dmarc, "dmarc_fail", "DMARC authentication failed."),
    ):
        if verdict is AuthenticationVerdict.FAIL:
            add_reason(code, description, (f"authentication.{protocol}=FAIL",))

    reply_mismatch, reply_refs = _reply_to_mismatch(parsed_email)
    if reply_mismatch:
        add_reason(
            "reply_to_domain_mismatch",
            "The sender and Reply-To domains differ.",
            reply_refs,
        )

    display_impersonation, display_refs = _display_name_impersonation(detection)
    if display_impersonation:
        add_reason(
            "display_name_impersonation",
            "Deterministic detection identified display-name impersonation evidence.",
            display_refs,
        )

    detection_signals = (
        (
            DetectionCategory.URGENCY,
            "urgency",
            "The message contains urgency or time-pressure language.",
        ),
        (
            DetectionCategory.CREDENTIAL_REQUEST,
            "credential_request",
            "The message requests credentials or account verification.",
        ),
        (
            DetectionCategory.PAYMENT_REQUEST,
            "payment_request",
            "The message requests a payment or payment-detail change.",
        ),
        (
            DetectionCategory.SUSPICIOUS_CALL_TO_ACTION,
            "suspicious_cta",
            "The message contains a suspicious call to action.",
        ),
        (
            DetectionCategory.BUSINESS_EMAIL_COMPROMISE,
            "bec",
            "Deterministic detection identified a business email compromise pattern.",
        ),
    )
    for category, code, description in detection_signals:
        findings = _findings_for(detection, category)
        if findings:
            add_reason(code, description, _finding_refs(findings))

    negative_url_findings = tuple(
        finding
        for finding in threat_intel.findings
        if finding.indicator_type is IOCType.URL and finding.verdict in _NEGATIVE_REPUTATION
    )
    if negative_url_findings:
        add_reason(
            "suspicious_url",
            "Threat intelligence reported a URL as suspicious or malicious.",
            _threat_refs(negative_url_findings),
        )

    negative_domain_findings = tuple(
        finding
        for finding in threat_intel.findings
        if finding.indicator_type is IOCType.DOMAIN
        and finding.verdict in _NEGATIVE_REPUTATION
    )
    if negative_domain_findings:
        add_reason(
            "negative_domain_reputation",
            "Threat intelligence reported negative domain reputation.",
            _threat_refs(negative_domain_findings),
        )

    negative_ip_findings = tuple(
        finding
        for finding in threat_intel.findings
        if finding.indicator_type is IOCType.IP_ADDRESS
        and finding.verdict in _NEGATIVE_REPUTATION
    )
    if negative_ip_findings:
        add_reason(
            "negative_ip_reputation",
            "Threat intelligence reported negative IP reputation.",
            _threat_refs(negative_ip_findings),
        )

    malicious_hash_findings = tuple(
        finding
        for finding in threat_intel.findings
        if finding.indicator_type is IOCType.ATTACHMENT_SHA256
        and finding.verdict is ReputationVerdict.MALICIOUS
    )
    if malicious_hash_findings:
        add_reason(
            "malicious_attachment_hash",
            "Threat intelligence matched an attachment SHA-256 to malicious intelligence.",
            _threat_refs(malicious_hash_findings),
        )

    raw_score = sum(reason.points for reason in reasons)
    score = min(raw_score, 100)
    return RiskResult(
        score=score,
        severity=_severity(score),
        reasons=tuple(reasons),
        formula_version=FORMULA_VERSION,
        unknown_inputs=_unknown_inputs(parsed_email, threat_intel),
    )


class DeterministicRiskEngine:
    """RiskEngine implementation using only the approved screening weights."""

    def score(
        self,
        *,
        parsed_email: ParsedEmail,
        detection: DetectionResult,
        threat_intel: ThreatIntelResult,
        geolocations: Sequence[GeoLocationResult],
    ) -> RiskResult:
        return calculate_risk(
            parsed_email=parsed_email,
            detection=detection,
            threat_intel=threat_intel,
            geolocations=geolocations,
        )
