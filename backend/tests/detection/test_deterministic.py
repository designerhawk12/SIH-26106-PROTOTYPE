"""Offline tests for deterministic Layer 2 threat detection."""

from __future__ import annotations

import asyncio
from hashlib import sha256
from pathlib import Path

from backend.app.schemas import DetectionCategory, DetectionResult, MailboxAddress, ParsedEmail
from backend.app.services.detection import DeterministicDetectionService, detect_email
from backend.app.services.email_forensics import EmailForensicsParser


FIXTURE_DIRECTORY = Path(__file__).resolve().parents[3] / "fixtures" / "emails"


def parsed_fixture(name: str) -> ParsedEmail:
    raw_email = (FIXTURE_DIRECTORY / name).read_bytes()
    return EmailForensicsParser().parse(raw_email)


def categories(result: DetectionResult) -> set[DetectionCategory]:
    return {finding.category for finding in result.findings}


def test_phishing_fixture_detects_urgency_credentials_cta_phishing_and_social_engineering() -> None:
    result = detect_email(parsed_fixture("02_phishing.eml"))

    assert {
        DetectionCategory.URGENCY,
        DetectionCategory.CREDENTIAL_REQUEST,
        DetectionCategory.SUSPICIOUS_CALL_TO_ACTION,
        DetectionCategory.PHISHING,
        DetectionCategory.SOCIAL_ENGINEERING,
        DetectionCategory.IMPERSONATION,
    } <= categories(result)
    assert all(finding.evidence for finding in result.findings)
    assert all(finding.explanation for finding in result.findings)


def test_bec_fixture_detects_payment_impersonation_bec_and_social_engineering() -> None:
    result = detect_email(parsed_fixture("03_bec.eml"))

    assert DetectionCategory.PAYMENT_REQUEST in categories(result)
    assert DetectionCategory.IMPERSONATION in categories(result)
    assert DetectionCategory.BUSINESS_EMAIL_COMPROMISE in categories(result)
    assert DetectionCategory.SOCIAL_ENGINEERING in categories(result)
    assert DetectionCategory.PHISHING not in categories(result)


def test_sender_reply_to_mismatch_from_forensics_is_evidence() -> None:
    result = detect_email(parsed_fixture("04_spoofed_sender.eml"))
    finding = next(
        item for item in result.findings if item.category is DetectionCategory.IMPERSONATION
    )

    assert any("Reply-To" in item or "reply-to" in item.lower() for item in finding.evidence)


def test_explicit_payment_and_invoice_manipulation_phrases() -> None:
    parsed = ParsedEmail(
        original_sha256=sha256(b"payment").hexdigest(),
        subject="Revised invoice payment",
        text_body="Please change the invoice and release the payment to the new bank details.",
        sender=MailboxAddress(display_name="Finance Director", address="finance@example.org"),
    )

    result = detect_email(parsed)
    assert DetectionCategory.PAYMENT_REQUEST in categories(result)
    assert DetectionCategory.BUSINESS_EMAIL_COMPROMISE in categories(result)


def test_legitimate_email_has_no_threat_findings() -> None:
    result = detect_email(parsed_fixture("01_legitimate.eml"))

    assert result.findings == ()


def test_legitimate_urgent_email_is_not_called_phishing() -> None:
    result = detect_email(parsed_fixture("07_legitimate_urgent.eml"))

    assert categories(result) == {DetectionCategory.URGENCY}
    assert DetectionCategory.PHISHING not in categories(result)
    assert DetectionCategory.SOCIAL_ENGINEERING not in categories(result)


def test_prompt_injection_is_treated_as_evidence_and_cannot_mark_itself_safe() -> None:
    parsed = parsed_fixture("08_prompt_injection.eml")
    result = detect_email(parsed)

    assert DetectionCategory.SOCIAL_ENGINEERING in categories(result)
    finding = next(
        item for item in result.findings if item.category is DetectionCategory.SOCIAL_ENGINEERING
    )
    assert any("Ignore previous" in evidence for evidence in finding.evidence)
    assert "no configured" not in (result.summary or "").lower()


def test_missing_and_partial_parsed_email_data_remains_supported() -> None:
    empty = ParsedEmail(original_sha256=sha256(b"").hexdigest())
    partial = ParsedEmail(
        original_sha256=sha256(b"partial").hexdigest(),
        text_body="Enter your password to validate your account.",
    )

    empty_result = detect_email(empty)
    partial_result = detect_email(partial)

    assert empty_result.findings == ()
    assert empty_result.warnings
    assert DetectionCategory.CREDENTIAL_REQUEST in categories(partial_result)


def test_detection_is_deterministically_repeatable() -> None:
    parsed = parsed_fixture("02_phishing.eml")

    first = detect_email(parsed)
    second = detect_email(parsed)

    assert first == second
    assert first.model_name == "deterministic_rules"
    assert first.model_version == "1.0.0"


def test_async_service_implements_existing_detection_boundary() -> None:
    parsed = parsed_fixture("03_bec.eml")

    result = asyncio.run(DeterministicDetectionService().detect(parsed))

    assert DetectionCategory.BUSINESS_EMAIL_COMPROMISE in categories(result)
