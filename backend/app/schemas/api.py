"""HTTP request/response envelope contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from .analysis import EmailAnalysis
from .email import ContractModel
from .enums import AnalysisStatus, RiskLevel


class CaseSummary(ContractModel):
    case_id: UUID
    status: AnalysisStatus
    original_filename: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    risk_score: int | None = Field(default=None, ge=0, le=100)
    risk_severity: RiskLevel | None = None
    subject: str | None = None


class CaseListResponse(ContractModel):
    items: tuple[CaseSummary, ...] = ()
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class AnalyzeCaseResponse(ContractModel):
    analysis: EmailAnalysis


class HealthResponse(ContractModel):
    status: Literal["ok"] = "ok"
    service: Literal["email-threat-platform"] = "email-threat-platform"
    version: str
    timestamp: datetime


class ErrorDetail(ContractModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(ContractModel):
    error: ErrorDetail
    request_id: str | None = None
