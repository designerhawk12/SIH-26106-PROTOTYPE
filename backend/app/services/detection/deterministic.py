"""Deterministic Layer 2 detection over untrusted parsed email evidence.

The detector performs string and metadata analysis only. It never executes an
attachment, visits an IOC, renders HTML, or interprets email text as commands.
"""

from __future__ import annotations

from html import escape
import re
from typing import Iterable, Pattern

from ...schemas import (
    AuthenticationVerdict,
    DetectionCategory,
    DetectionFinding,
    DetectionResult,
    IOCType,
    ParsedEmail,
    Severity,
)


DETECTOR_NAME = "deterministic_rules"
DETECTOR_VERSION = "1.0.0"
_MAX_EVIDENCE_ITEMS = 3
_MAX_EVIDENCE_LENGTH = 180


def _patterns(*expressions: str) -> tuple[Pattern[str], ...]:
    return tuple(re.compile(expression, re.IGNORECASE) for expression in expressions)


_URGENCY_PATTERNS = _patterns(
    r"\b(?:urgent|immediately|asap|right away|time[- ]sensitive)\b",
    r"\baction required\b",
    r"\bbefore (?:today(?:'s)?|the deadline|close of business)\b",
)
_CREDENTIAL_PATTERNS = _patterns(
    r"\b(?:verify|confirm|validate|restore|unlock|reactivate|secure)\s+"
    r"(?:your\s+)?(?:account|password|credentials?|mailbox|login|sign[- ]?in)\b",
    r"\b(?:enter|provide|send|share|submit)\s+(?:your\s+)?"
    r"(?:password|credentials?|login|verification code|one[- ]time (?:password|code))\b",
    r"\b(?:password|account|mailbox)\s+(?:verification|validation|reset)\b",
)
_PAYMENT_PATTERNS = _patterns(
    r"\b(?:updated?|changed?|new|revised)\s+(?:bank|payment|wire|remittance)\s+"
    r"(?:details|instructions|account)\b",
    r"\b(?:send|make|process|release|approve|authorize|redirect)\s+"
    r"(?:the\s+|this\s+|a\s+)?(?:payment|wire|bank transfer|invoice payment)\b",
    r"\b(?:supplier|vendor|beneficiary)\s+account\s+(?:details|information)\b",
    r"\b(?:gift cards?|wire transfer|payment run)\b",
    r"\b(?:change|update|replace)\s+(?:the\s+)?(?:invoice|payment|bank)\b",
)
_CTA_PATTERNS = _patterns(
    r"\bclick\s+(?:here|the\s+(?:link|button)|this\s+link)\b",
    r"\b(?:sign|log)[ -]?in\s+(?:here|now|to)\b",
    r"\bverify\s+(?:your\s+)?(?:account|mailbox|identity|login)\b",
    r"\b(?:download|open)\s+(?:the\s+)?(?:attachment|document|invoice)\b",
    r"\breply\s+with\s+(?:your\s+)?(?:password|credentials?|code|bank details)\b",
)
_MANIPULATION_PATTERNS = _patterns(
    r"\bdo not (?:tell|contact|discuss|share)\b",
    r"\bkeep (?:this|it) confidential\b",
    r"\b(?:trust me|act now|final warning|avoid suspension)\b",
    r"\bignore previous (?:instructions|security instructions|messages)\b",
    r"\bmark this (?:message|email) as safe\b",
)
_AUTHORITY_TERMS = _patterns(
    r"\b(?:ceo|cfo|chief executive|finance director|executive office|president|payroll)\b",
    r"\b(?:account security|security team|help ?desk|administrator)\b",
)


def _searchable_fields(parsed_email: ParsedEmail) -> tuple[tuple[str, str], ...]:
    """Return hostile content as labelled strings without rendering or evaluating it."""

    fields = (
        ("Subject", parsed_email.subject),
        ("Text body", parsed_email.text_body),
        ("HTML body", parsed_email.html_body_untrusted),
    )
    return tuple((label, value) for label, value in fields if value)


def _matches(patterns: Iterable[Pattern[str]], fields: tuple[tuple[str, str], ...]) -> bool:
    return any(pattern.search(value) for _, value in fields for pattern in patterns)


def _safe_excerpt(label: str, value: str, match: re.Match[str]) -> str:
    start = max(0, match.start() - 55)
    end = min(len(value), match.end() + 75)
    excerpt = " ".join(value[start:end].split())
    if start:
        excerpt = f"...{excerpt}"
    if end < len(value):
        excerpt = f"{excerpt}..."
    return f"{label}: {escape(excerpt)[:_MAX_EVIDENCE_LENGTH]}"


def _evidence(
    patterns: Iterable[Pattern[str]], fields: tuple[tuple[str, str], ...]
) -> tuple[str, ...]:
    evidence: list[str] = []
    for label, value in fields:
        for pattern in patterns:
            match = pattern.search(value)
            if match:
                item = _safe_excerpt(label, value, match)
                if item not in evidence:
                    evidence.append(item)
                if len(evidence) == _MAX_EVIDENCE_ITEMS:
                    return tuple(evidence)
    return tuple(evidence)


def _domain(address: str) -> str | None:
    if address.count("@") != 1:
        return None
    return address.rsplit("@", 1)[1].lower().rstrip(".") or None


def _sender_reply_mismatch(parsed_email: ParsedEmail) -> bool:
    if not parsed_email.sender or not parsed_email.reply_to:
        return any(
            "from and reply-to domains differ" in warning.lower()
            for warning in parsed_email.parse_warnings
        )
    sender_domain = _domain(parsed_email.sender.address)
    reply_domains = {_domain(mailbox.address) for mailbox in parsed_email.reply_to}
    reply_domains.discard(None)
    return bool(sender_domain and reply_domains and any(sender_domain != item for item in reply_domains))


def _authentication_failed(parsed_email: ParsedEmail) -> bool:
    concerning = {AuthenticationVerdict.FAIL, AuthenticationVerdict.SOFTFAIL}
    auth = parsed_email.authentication
    return auth.spf in concerning or auth.dkim in concerning or auth.dmarc in concerning


def _has_url(parsed_email: ParsedEmail) -> bool:
    return any(ioc.type is IOCType.URL for ioc in parsed_email.iocs)


def _finding(
    category: DetectionCategory,
    severity: Severity,
    confidence: float,
    title: str,
    explanation: str,
    evidence: tuple[str, ...],
) -> DetectionFinding:
    return DetectionFinding(
        finding_id=f"det-{category.value.lower().replace('_', '-')}",
        category=category,
        severity=severity,
        confidence=confidence,
        title=title,
        explanation=explanation,
        evidence=evidence,
        detector=f"{DETECTOR_NAME}:{DETECTOR_VERSION}",
    )


def detect_email(parsed_email: ParsedEmail) -> DetectionResult:
    """Return repeatable, evidence-backed findings without network or model access."""

    fields = _searchable_fields(parsed_email)
    urgency = _matches(_URGENCY_PATTERNS, fields)
    credential = _matches(_CREDENTIAL_PATTERNS, fields)
    payment = _matches(_PAYMENT_PATTERNS, fields)
    suspicious_cta = _matches(_CTA_PATTERNS, fields)
    manipulation = _matches(_MANIPULATION_PATTERNS, fields)
    authority = _matches(_AUTHORITY_TERMS, fields) or bool(
        parsed_email.sender
        and parsed_email.sender.display_name
        and _matches(_AUTHORITY_TERMS, (("Sender display name", parsed_email.sender.display_name),))
    )
    sender_mismatch = _sender_reply_mismatch(parsed_email)
    auth_failed = _authentication_failed(parsed_email)
    has_url = _has_url(parsed_email)

    findings: list[DetectionFinding] = []
    if urgency:
        findings.append(
            _finding(
                DetectionCategory.URGENCY,
                Severity.LOW,
                0.82,
                "Urgency or time pressure",
                "The message uses time-pressure language. Urgency is contextual evidence and is not, by itself, a phishing verdict.",
                _evidence(_URGENCY_PATTERNS, fields),
            )
        )
    if credential:
        findings.append(
            _finding(
                DetectionCategory.CREDENTIAL_REQUEST,
                Severity.HIGH,
                0.91,
                "Credential or account verification request",
                "The message asks the recipient to verify an account or provide authentication information.",
                _evidence(_CREDENTIAL_PATTERNS, fields),
            )
        )
    if payment:
        findings.append(
            _finding(
                DetectionCategory.PAYMENT_REQUEST,
                Severity.MEDIUM,
                0.88,
                "Payment or invoice manipulation language",
                "The message requests a payment action or a change to payment, invoice, bank, or supplier-account information.",
                _evidence(_PAYMENT_PATTERNS, fields),
            )
        )
    if suspicious_cta:
        findings.append(
            _finding(
                DetectionCategory.SUSPICIOUS_CALL_TO_ACTION,
                Severity.MEDIUM,
                0.86,
                "Suspicious call to action",
                "The message directs the recipient toward an account, credential, link, attachment, or sensitive-data action.",
                _evidence(_CTA_PATTERNS, fields),
            )
        )

    impersonation = sender_mismatch or (authority and auth_failed)
    if impersonation:
        mismatch_evidence = tuple(
            warning
            for warning in parsed_email.parse_warnings
            if "from and reply-to domains differ" in warning.lower()
        )
        if sender_mismatch and not mismatch_evidence and parsed_email.sender:
            replies = ", ".join(mailbox.address for mailbox in parsed_email.reply_to)
            mismatch_evidence = (
                f"Sender/Reply-To domains differ: {parsed_email.sender.address} -> {replies}",
            )
        display_evidence = _evidence(_AUTHORITY_TERMS, fields)
        if authority and parsed_email.sender and parsed_email.sender.display_name:
            display_evidence = (
                *display_evidence,
                f"Sender display name: {escape(parsed_email.sender.display_name)[:120]}",
            )
        findings.append(
            _finding(
                DetectionCategory.IMPERSONATION,
                Severity.HIGH,
                0.92 if sender_mismatch else 0.8,
                "Sender identity inconsistency",
                "The supplied forensic evidence shows a sender/Reply-To mismatch or an authority-style display name combined with failed authentication.",
                tuple(dict.fromkeys((*mismatch_evidence, *display_evidence)))[:_MAX_EVIDENCE_ITEMS],
            )
        )

    bec = payment and (sender_mismatch or authority or manipulation)
    if bec:
        findings.append(
            _finding(
                DetectionCategory.BUSINESS_EMAIL_COMPROMISE,
                Severity.HIGH,
                0.93,
                "Business email compromise pattern",
                "Payment-change language appears with identity inconsistency, authority framing, or coercive language characteristic of BEC attempts.",
                tuple(
                    dict.fromkeys(
                        (*_evidence(_PAYMENT_PATTERNS, fields), *_evidence(_MANIPULATION_PATTERNS, fields))
                    )
                )[:_MAX_EVIDENCE_ITEMS],
            )
        )

    phishing = credential and suspicious_cta and (
        urgency or sender_mismatch or auth_failed or has_url
    )
    if phishing:
        findings.append(
            _finding(
                DetectionCategory.PHISHING,
                Severity.HIGH,
                0.94,
                "Phishing evidence cluster",
                "A credential-focused call to action is reinforced by urgency, identity inconsistency, authentication failure, or a URL indicator.",
                tuple(
                    dict.fromkeys(
                        (*_evidence(_CREDENTIAL_PATTERNS, fields), *_evidence(_CTA_PATTERNS, fields))
                    )
                )[:_MAX_EVIDENCE_ITEMS],
            )
        )

    social_engineering = manipulation or (urgency and (credential or payment or suspicious_cta)) or (
        authority and payment
    )
    if social_engineering:
        social_patterns = (*_MANIPULATION_PATTERNS, *_URGENCY_PATTERNS, *_AUTHORITY_TERMS)
        findings.append(
            _finding(
                DetectionCategory.SOCIAL_ENGINEERING,
                Severity.MEDIUM,
                0.89,
                "Social-engineering language",
                "The message combines coercion, urgency, authority, or instruction-override language with an attempted recipient action.",
                _evidence(social_patterns, fields),
            )
        )

    warnings = () if fields else ("No subject or body content was available for content rules.",)
    category_names = ", ".join(finding.category.value for finding in findings)
    summary = (
        f"Deterministic analysis produced {len(findings)} finding(s): {category_names}."
        if findings
        else "Deterministic analysis found no configured threat-language patterns."
    )
    return DetectionResult(
        findings=tuple(findings),
        model_name=DETECTOR_NAME,
        model_version=DETECTOR_VERSION,
        summary=summary,
        warnings=warnings,
    )


class DeterministicDetectionService:
    """Async service adapter used by the application orchestration boundary."""

    async def detect(self, parsed_email: ParsedEmail) -> DetectionResult:
        return detect_email(parsed_email)
