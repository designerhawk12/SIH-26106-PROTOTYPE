"""Case ingestion, retrieval, listing, and reporting endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from ...core import AppError, Settings
from ...core.uploads import read_bounded_upload, safe_eml_filename
from ...db import CaseRepository
from ...schemas import (
    AnalysisStatus,
    AnalyzeCaseResponse,
    CaseListResponse,
    CaseSummary,
    EmailAnalysis,
    RiskLevel,
)
from ...services.orchestrator import EmailAnalysisError
from ...services.orchestrator.interfaces import AnalysisOrchestrator
from ...services.reporting.interfaces import ReportingService
from ..dependencies import (
    get_analysis_orchestrator,
    get_case_repository,
    get_reporting_service,
    get_runtime_settings,
)

router = APIRouter(prefix="/api/v1/cases", tags=["Cases"])


def _case_subject(analysis_json: dict[str, Any]) -> str | None:
    parsed = analysis_json.get("parsed_email")
    if not isinstance(parsed, dict):
        return None
    subject = parsed.get("subject")
    return subject if isinstance(subject, str) else None


def _case_completed_at(analysis_json: dict[str, Any]) -> datetime | None:
    value = analysis_json.get("completed_at")
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@router.post(
    "/analyze",
    response_model=AnalyzeCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_case(
    file: Annotated[UploadFile, File(description="RFC 5322 .eml upload")],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    orchestrator: Annotated[AnalysisOrchestrator, Depends(get_analysis_orchestrator)],
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
) -> AnalyzeCaseResponse:
    filename = safe_eml_filename(file.filename)
    raw_email = await read_bounded_upload(file, settings.max_upload_bytes)
    try:
        analysis = await orchestrator.analyze(raw_email, original_filename=filename)
    except EmailAnalysisError as exc:
        raise AppError(
            status_code=422,
            code="INVALID_EMAIL",
            message="The uploaded file could not be parsed as an email.",
            field="file",
        ) from exc
    try:
        await run_in_threadpool(repository.create, analysis)
    except Exception as exc:
        raise AppError(
            status_code=500,
            code="CASE_PERSISTENCE_FAILED",
            message="The analysis could not be stored.",
        ) from exc
    return AnalyzeCaseResponse(analysis=analysis)


@router.get("", response_model=CaseListResponse)
async def list_cases(
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CaseListResponse:
    rows = await run_in_threadpool(repository.list, limit=limit, offset=offset)
    total = await run_in_threadpool(repository.count)
    items = tuple(
        CaseSummary(
            case_id=row.id,
            status=AnalysisStatus(row.status),
            original_filename=row.filename,
            created_at=row.created_at,
            completed_at=_case_completed_at(row.analysis_json),
            risk_score=row.risk_score,
            risk_severity=RiskLevel(row.severity) if row.severity else None,
            subject=_case_subject(row.analysis_json),
        )
        for row in rows
    )
    return CaseListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{case_id}", response_model=EmailAnalysis)
async def get_case(
    case_id: UUID,
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
) -> EmailAnalysis:
    analysis = await run_in_threadpool(repository.get_analysis, case_id)
    if analysis is None:
        raise AppError(
            status_code=404,
            code="CASE_NOT_FOUND",
            message="The requested case was not found.",
        )
    return analysis


@router.get("/{case_id}/report", response_class=Response)
async def get_case_report(
    case_id: UUID,
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    reporting: Annotated[ReportingService, Depends(get_reporting_service)],
) -> Response:
    analysis = await run_in_threadpool(repository.get_analysis, case_id)
    if analysis is None:
        raise AppError(
            status_code=404,
            code="CASE_NOT_FOUND",
            message="The requested case was not found.",
        )
    if analysis.status in {AnalysisStatus.RECEIVED, AnalysisStatus.PROCESSING}:
        raise AppError(
            status_code=409,
            code="REPORT_NOT_READY",
            message="The case is not ready for reporting.",
        )
    try:
        report_bytes = await reporting.render_pdf(analysis)
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="REPORT_GENERATION_FAILED",
            message="The forensic report is temporarily unavailable.",
        ) from exc
    return Response(
        content=report_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="case-{analysis.case_id}.pdf"'
        },
    )
