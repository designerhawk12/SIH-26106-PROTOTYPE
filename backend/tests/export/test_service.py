"""Tests for the evidence export service."""

import io
import json
import uuid
import zipfile
from datetime import datetime, timezone

import pytest

from backend.app.schemas import (
    AnalysisStatus,
    EmailAnalysis,
    ParsedEmail,
    MailboxAddress,
    AttachmentEvidence,
    RiskResult,
    RiskLevel,
    ThreatIntelResult,
)
from backend.app.schemas.enums import EnrichmentStatus
from backend.app.services.export.factory import build_export_service


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
            sent_at=datetime.now(timezone.utc),
            message_id="<123@evil.com>",
            original_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            attachments=(
                AttachmentEvidence(
                    attachment_id="att-1",
                    filename="invoice.pdf",
                    content_type="application/pdf",
                    size_bytes=1024,
                    sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                ),
                AttachmentEvidence(
                    attachment_id="att-2",
                    filename="../../../etc/passwd", # Path traversal attempt
                    content_type="text/plain",
                    size_bytes=512,
                    sha256="0987654321fedcba0987654321fedcba0987654321fedcba0987654321fedcba",
                )
            )
        ),
        risk=RiskResult(
            score=85,
            severity=RiskLevel.HIGH,
            formula_version="1.0"
        ),
    )


@pytest.mark.asyncio
async def test_successful_zip_generation_content_and_safety(mock_analysis: EmailAnalysis):
    service = build_export_service()
    zip_bytes = await service.export_case(mock_analysis)
    
    assert isinstance(zip_bytes, bytes)
    
    # 5. ZIP can be opened successfully
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        namelist = zf.namelist()
        
        # 6. manifest.json exists
        assert "manifest.json" in namelist
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["case_id"] == str(mock_analysis.case_id)
        assert manifest["analysis_status"] == AnalysisStatus.COMPLETED.value
        assert manifest["original_email_stored"] is False
        assert "original_email_sha256" in manifest
        
        # 7. analysis.json exists
        assert "analysis.json" in namelist
        analysis_data = json.loads(zf.read("analysis.json"))
        assert analysis_data["case_id"] == str(mock_analysis.case_id)
        
        # 8. hashes.txt exists
        assert "hashes.txt" in namelist
        hashes_txt = zf.read("hashes.txt").decode("utf-8")
        # 10. original email SHA-256 is preserved
        assert "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" in hashes_txt
        # 11. attachment hashes are preserved
        assert "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890" in hashes_txt
        assert "invoice.pdf" in hashes_txt
        
        # 15. malicious filenames cannot create path traversal ZIP entries
        # The attachment JSON should contain it, but we never create files named after it
        assert "attachments.json" in namelist
        attachments = json.loads(zf.read("attachments.json"))
        assert len(attachments) == 2
        assert any(a["filename"] == "../../../etc/passwd" for a in attachments)
        
        # Ensure no arbitrary files were created with traversal
        assert "../../../etc/passwd" not in namelist


@pytest.mark.asyncio
async def test_partial_enrichment_does_not_fail(mock_analysis: EmailAnalysis):
    # 12. partial enrichment does not fail
    mock_analysis = mock_analysis.model_copy(update={
        "status": AnalysisStatus.PARTIAL,
        "threat_intel": ThreatIntelResult(
            status=EnrichmentStatus.UNAVAILABLE,
            provider_errors=("VirusTotal is down",)
        )
    })
    
    service = build_export_service()
    zip_bytes = await service.export_case(mock_analysis)
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        namelist = zf.namelist()
        assert "manifest.json" in namelist
        manifest = json.loads(zf.read("manifest.json"))
        assert "threat-intel.json" in manifest["files_unavailable"]
        assert "threat-intel.json" not in namelist


@pytest.mark.asyncio
async def test_forbidden_services_are_not_called(mock_analysis: EmailAnalysis, monkeypatch: pytest.MonkeyPatch):
    # 16. export does not rerun analysis
    # 17. export does not call external providers
    import urllib.request
    
    def mock_urlopen(*args, **kwargs):
        raise RuntimeError("Network calls are forbidden during evidence export")
        
    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
    
    # We monkeypatch the risk engine to ensure it's not called
    from backend.app.services.risk.engine import DeterministicRiskEngine
    def mock_score(*args, **kwargs):
        raise RuntimeError("Risk engine must not be called")
    monkeypatch.setattr(DeterministicRiskEngine, "score", mock_score)
    
    service = build_export_service()
    zip_bytes = await service.export_case(mock_analysis)
    assert zip_bytes
