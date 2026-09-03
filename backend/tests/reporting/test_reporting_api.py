import io
import uuid
from typing import Any
from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.schemas import AnalysisStatus, EmailAnalysis
from backend.app.core import Settings
from backend.app.db import create_database_engine
from backend.main import create_app
from backend.app.services.reporting.interfaces import ReportingService
from backend.tests.auth_helpers import AUTH_HEADERS, FakeIdentityVerifier

class MockReportingService(ReportingService):
    async def render_pdf(self, analysis: EmailAnalysis) -> bytes:
        return b"%PDF-mock"


@pytest.fixture
def mock_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_analysis = MagicMock()
    return repo


@pytest.fixture
def app_client(mock_repo: MagicMock) -> tuple[FastAPI, TestClient]:
    # We override the dependencies directly on the app instance
    app = create_app(
        settings=Settings(database_url="sqlite://"),
        database_engine=create_database_engine("sqlite://"),
        reporting_service=MockReportingService(),
        identity_verifier=FakeIdentityVerifier(),
    )
    
    # Let's override the repository dependency
    from backend.app.api.dependencies import get_case_repository
    
    def override_get_repo():
        yield mock_repo
        
    app.dependency_overrides[get_case_repository] = override_get_repo
    with TestClient(app, headers=AUTH_HEADERS) as client:
        yield app, client


def test_missing_case_returns_404(app_client: tuple[FastAPI, TestClient], mock_repo: MagicMock):
    _, client = app_client
    mock_repo.get_analysis.return_value = None
    
    random_uuid = uuid.uuid4()
    response = client.get(f"/api/v1/cases/{random_uuid}/report")
    
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CASE_NOT_FOUND"


def test_report_endpoint_returns_200_and_correct_headers(app_client: tuple[FastAPI, TestClient], mock_repo: MagicMock):
    _, client = app_client
    case_id = uuid.uuid4()
    
    # Create a mock EmailAnalysis to return
    from datetime import datetime, timezone
    mock_analysis = EmailAnalysis(
        case_id=case_id,
        status=AnalysisStatus.COMPLETED,
        created_at=datetime.now(timezone.utc),
    )
    mock_repo.get_analysis.return_value = mock_analysis
    
    response = client.get(f"/api/v1/cases/{case_id}/report")
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert f'filename="case-{case_id}.pdf"' in response.headers["Content-Disposition"]
    assert response.content == b"%PDF-mock"


def test_report_not_ready_returns_409(app_client: tuple[FastAPI, TestClient], mock_repo: MagicMock):
    _, client = app_client
    case_id = uuid.uuid4()
    
    from datetime import datetime, timezone
    mock_analysis = EmailAnalysis(
        case_id=case_id,
        status=AnalysisStatus.PROCESSING,
        created_at=datetime.now(timezone.utc),
    )
    mock_repo.get_analysis.return_value = mock_analysis
    
    response = client.get(f"/api/v1/cases/{case_id}/report")
    
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REPORT_NOT_READY"


def test_partial_case_returns_200(app_client: tuple[FastAPI, TestClient], mock_repo: MagicMock):
    _, client = app_client
    case_id = uuid.uuid4()
    
    from datetime import datetime, timezone
    mock_analysis = EmailAnalysis(
        case_id=case_id,
        status=AnalysisStatus.PARTIAL,
        created_at=datetime.now(timezone.utc),
    )
    mock_repo.get_analysis.return_value = mock_analysis
    
    response = client.get(f"/api/v1/cases/{case_id}/report")
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.content == b"%PDF-mock"
