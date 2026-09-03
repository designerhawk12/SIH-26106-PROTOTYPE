"""Case ingestion, retrieval, listing, and reporting endpoints."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any, TypeVar
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
    Permission,
    RiskLevel,
    UserProfile,
)
from ...services.export.interfaces import EvidenceExportService
from ...services.orchestrator import EmailAnalysisError
from ...services.orchestrator.interfaces import AnalysisOrchestrator
from ...services.reporting.interfaces import ReportingService
from ..dependencies import (
    get_analysis_orchestrator,
    get_case_repository,
    get_export_service,
    get_reporting_service,
    get_runtime_settings,
    require_permission,
)

router = APIRouter(prefix="/api/v1/cases", tags=["Cases"])
T = TypeVar("T")


async def _run_database_operation(
    operation: Callable[..., T], *args: object, **kwargs: object
) -> T:
    """Run repository work without leaking connection details on failure."""

    try:
        return await run_in_threadpool(operation, *args, **kwargs)
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="Case persistence is temporarily unavailable.",
        ) from exc


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
    _user: Annotated[
        UserProfile, Depends(require_permission(Permission.ANALYZE_EMAILS))
    ],
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
    await _run_database_operation(repository.create, analysis)
    return AnalyzeCaseResponse(analysis=analysis)


@router.get("", response_model=CaseListResponse)
async def list_cases(
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    _user: Annotated[
        UserProfile, Depends(require_permission(Permission.INSPECT_CASES))
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CaseListResponse:
    rows = await _run_database_operation(repository.list, limit=limit, offset=offset)
    total = await _run_database_operation(repository.count)
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
    _user: Annotated[
        UserProfile, Depends(require_permission(Permission.INSPECT_CASES))
    ],
) -> EmailAnalysis:
    analysis = await _run_database_operation(repository.get_analysis, case_id)
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
    _user: Annotated[
        UserProfile, Depends(require_permission(Permission.GENERATE_REPORTS))
    ],
) -> Response:
    analysis = await _run_database_operation(repository.get_analysis, case_id)
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


@router.get("/{case_id}/evidence", response_class=Response)
async def get_case_evidence(
    case_id: UUID,
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    export_svc: Annotated[EvidenceExportService, Depends(get_export_service)],
    _user: Annotated[
        UserProfile, Depends(require_permission(Permission.EXPORT_EVIDENCE))
    ],
) -> Response:
    analysis = await _run_database_operation(repository.get_analysis, case_id)
    if analysis is None:
        raise AppError(
            status_code=404,
            code="CASE_NOT_FOUND",
            message="The requested case was not found.",
        )
    if analysis.status in {AnalysisStatus.RECEIVED, AnalysisStatus.PROCESSING}:
        raise AppError(
            status_code=409,
            code="EVIDENCE_NOT_READY",
            message="The case is not ready for evidence export.",
        )
    try:
        zip_bytes = await export_svc.export_case(analysis)
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="EVIDENCE_EXPORT_FAILED",
            message="The forensic evidence export is temporarily unavailable.",
        ) from exc
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="sentinel-mx-case-{analysis.case_id}-evidence.zip"'
        },
    )
