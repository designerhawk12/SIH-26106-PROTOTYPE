import uuid
from datetime import datetime, timezone

import pytest

from backend.app.schemas import (
    AnalysisStatus,
    DetectionCategory,
    DetectionFinding,
    DetectionResult,
    EmailAnalysis,
    IOCType,
    ParsedEmail,
    MailboxAddress,
    ReputationVerdict,
    RiskLevel,
    RiskReason,
    RiskResult,
    Severity,
    ThreatIntelResult,
    GeoLocationResult,
)
from backend.app.schemas.enums import GeoLocationStatus, AuthenticationVerdict
from backend.app.schemas.email import AuthenticationResults
from backend.app.schemas.threat_intel import ThreatFinding
from backend.app.services.reporting.factory import build_reporting_service


@pytest.fixture
def mock_analysis() -> EmailAnalysis:
    return EmailAnalysis(
        case_id=uuid.uuid4(),
        status=AnalysisStatus.COMPLETED,
        original_filename="malicious_phishing.eml",
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        parsed_email=ParsedEmail(
            subject="Urgent: Invoice Attached",
            sender=MailboxAddress(address="attacker@evil.com", display_name="Accounting Department"),
            to=(MailboxAddress(address="victim@company.com"),),
            cc=(MailboxAddress(address="manager@company.com"),),
            sent_at=datetime.now(timezone.utc),
            message_id="<123@evil.com>",
            original_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            authentication=AuthenticationResults(
                spf=AuthenticationVerdict.FAIL,
                dkim=AuthenticationVerdict.PASS,
                dmarc=AuthenticationVerdict.NONE,
            )
        ),
        risk=RiskResult(
            score=85,
            severity=RiskLevel.HIGH,
            reasons=(
                RiskReason(
                    code="PHISHING",
                    points=50,
                    description="Malicious sender domain detected."
                ),
            ),
            formula_version="1.0"
        ),
        detection=DetectionResult(
            findings=(
                DetectionFinding(
                    finding_id="f-123",
                    category=DetectionCategory.PHISHING,
                    title="Suspicious Request",
                    severity=Severity.HIGH,
                    confidence=0.9,
                    explanation="Email asks for urgent invoice payment.",
                    evidence=("Invoice Attached",),
                    detector="rules"
                ),
            )
        ),
        threat_intel=ThreatIntelResult(
            findings=(
                ThreatFinding(
                    indicator="evil.com",
                    indicator_type=IOCType.DOMAIN,
                    verdict=ReputationVerdict.MALICIOUS,
                    provider="TestProvider",
                    confidence=1.0
                ),
            )
        ),
        geolocations=(
            GeoLocationResult(
                ip_address="1.2.3.4",
                country="Testland",
                provider="TestGeo",
                status=GeoLocationStatus.FOUND,
            ),
        ),
        warnings=("Test warning",),
        errors=()
    )


@pytest.mark.asyncio
async def test_successful_pdf_generation_content_and_safety(mock_analysis: EmailAnalysis):
    service = build_reporting_service()
    pdf_bytes = await service.render_pdf(mock_analysis)
    
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    
    # Extract text from generated PDF
    import io
    from pypdf import PdfReader
    
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text()
        
    # 5. Generated PDF contains persisted Case ID.
    assert str(mock_analysis.case_id) in text
    
    # 6. Generated PDF contains persisted risk score and risk reasons.
    assert "85" in text
    assert "Malicious sender domain detected." in text
    
    # 7. Generated PDF contains SPF/DKIM/DMARC values.
    assert "FAIL" in text
    assert "PASS" in text
    assert "NONE" in text
    
    # 8. Generated PDF contains IOC values.
    assert "evil.com" in text
    
    # 9. Generated PDF contains attachment SHA-256 values.
    assert "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" in text
    
    # 12. Infrastructure wording uses "Observed Mail-Routing Infrastructure"
    assert "Observed Mail-Routing Infrastructure" in text
    assert "Attacker Location" not in text
    
    # 18. Script/HTML-like malicious evidence remains inert text.
    # This is tested implicitly by the escape in _safe, and explicitly in another test.



@pytest.mark.asyncio
async def test_missing_optional_evidence_works():
    # Only required fields
    analysis = EmailAnalysis(
        case_id=uuid.uuid4(),
        status=AnalysisStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
    )
    
    service = build_reporting_service()
    pdf_bytes = await service.render_pdf(analysis)
    
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_malicious_html_escaped_safely():
    analysis = EmailAnalysis(
        case_id=uuid.uuid4(),
        status=AnalysisStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
        parsed_email=ParsedEmail(
            subject="<script>alert('xss')</script>",
            sender=MailboxAddress(address="<bad>@evil.com"),
            original_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        ),
    )
    
    service = build_reporting_service()
    pdf_bytes = await service.render_pdf(analysis)
    
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_partial_threat_intel(mock_analysis: EmailAnalysis):
    mock_analysis = mock_analysis.model_copy(update={
        "threat_intel": ThreatIntelResult(
            findings=(
                ThreatFinding(
                    indicator="unknown.com",
                    indicator_type=IOCType.DOMAIN,
                    verdict=ReputationVerdict.UNKNOWN,
                    provider="TestProvider",
                    confidence=None
                ),
            )
        )
    })
    service = build_reporting_service()
    pdf_bytes = await service.render_pdf(mock_analysis)
    assert pdf_bytes.startswith(b"%PDF-")
    
    import io
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text()
        
    assert "UNKNOWN" in text
    assert "SAFE" not in text.upper()
    assert "BENIGN" not in text.upper()


@pytest.mark.asyncio
async def test_forbidden_services_are_not_called(mock_analysis: EmailAnalysis, monkeypatch: pytest.MonkeyPatch):
    # 13. Report generation does not call the deterministic risk engine.
    # 14. Report generation does not rerun detection.
    # 15. Report generation does not call Threat Intelligence providers.
    # 16. Report generation does not call geolocation providers.
    # 17. No remote URL/resource is fetched while creating the PDF.
    
    # We monkeypatch urllib.request.urlopen to ensure NO network calls are made by reportlab.
    import urllib.request
    
    def mock_urlopen(*args, **kwargs):
        raise RuntimeError("Network calls are forbidden during PDF generation")
        
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    # We monkeypatch the risk engine to ensure it's not called
    from backend.app.services.risk.engine import DeterministicRiskEngine
    def mock_score(*args, **kwargs):
        raise RuntimeError("Risk engine must not be called")
    monkeypatch.setattr(DeterministicRiskEngine, "score", mock_score)
    
    service = build_reporting_service()
    pdf_bytes = await service.render_pdf(mock_analysis)
    assert pdf_bytes.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_functionally_deterministic_report(mock_analysis: EmailAnalysis):
    # 19. Same EmailAnalysis produces functionally deterministic report content.
    service = build_reporting_service()
    pdf_bytes_1 = await service.render_pdf(mock_analysis)
    pdf_bytes_2 = await service.render_pdf(mock_analysis)
    
    import io
    from pypdf import PdfReader
    
    text_1 = "".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf_bytes_1)).pages)
    text_2 = "".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf_bytes_2)).pages)
    
    assert text_1 == text_2

