"""Tests for evidence export API endpoints."""

import io
import uuid
import zipfile
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.schemas import AnalysisStatus, EmailAnalysis
from backend.main import create_app
from backend.app.services.export.interfaces import EvidenceExportService


class MockExportService(EvidenceExportService):
    async def export_case(self, analysis: EmailAnalysis) -> bytes:
        return b"mock-zip-content"


@pytest.fixture
def mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_analysis = MagicMock()
    return repo


@pytest.fixture
def app_client(mock_repo: MagicMock) -> tuple[FastAPI, TestClient]:
    app = create_app()
    app.state.export_service = MockExportService()
    
    from backend.app.api.dependencies import get_case_repository
    
    def override_get_repo():
        yield mock_repo
        
    app.dependency_overrides[get_case_repository] = override_get_repo
    client = TestClient(app)
    return app, client


def test_missing_case_returns_404(app_client: tuple[FastAPI, TestClient], mock_repo: MagicMock):
    _, client = app_client
    mock_repo.get_analysis.return_value = None
    
    random_uuid = uuid.uuid4()
    response = client.get(f"/api/v1/cases/{random_uuid}/evidence")
    
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CASE_NOT_FOUND"


def test_export_endpoint_returns_200_and_correct_headers(app_client: tuple[FastAPI, TestClient], mock_repo: MagicMock):
    _, client = app_client
    case_id = uuid.uuid4()
    
    mock_analysis = EmailAnalysis(
        case_id=case_id,
        status=AnalysisStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
    )
    mock_repo.get_analysis.return_value = mock_analysis
    
    response = client.get(f"/api/v1/cases/{case_id}/evidence")
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"
    assert response.headers["Content-Disposition"] == f'attachment; filename="sentinel-mx-case-{case_id}-evidence.zip"'
    assert response.content == b"mock-zip-content"


def test_export_not_ready_returns_409(app_client: tuple[FastAPI, TestClient], mock_repo: MagicMock):
    _, client = app_client
    case_id = uuid.uuid4()
    
    mock_analysis = EmailAnalysis(
        case_id=case_id,
        status=AnalysisStatus.PROCESSING,
        created_at=datetime.now(timezone.utc),
    )
    mock_repo.get_analysis.return_value = mock_analysis
    
    response = client.get(f"/api/v1/cases/{case_id}/evidence")
    
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVIDENCE_NOT_READY"


def test_partial_case_returns_200(app_client: tuple[FastAPI, TestClient], mock_repo: MagicMock):
    _, client = app_client
    case_id = uuid.uuid4()
    
    mock_analysis = EmailAnalysis(
        case_id=case_id,
        status=AnalysisStatus.PARTIAL,
        created_at=datetime.now(timezone.utc),
    )
    mock_repo.get_analysis.return_value = mock_analysis
    
    response = client.get(f"/api/v1/cases/{case_id}/evidence")
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"
