"""FastAPI dependency adapters for infrastructure-owned components."""

from collections.abc import Iterator
from typing import cast

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from ..core import AppError, Settings
from ..db import CaseRepository, SqlAlchemyCaseRepository
from ..services.orchestrator.factory import build_default_analysis_orchestrator
from ..services.orchestrator.interfaces import AnalysisOrchestrator
from ..services.reporting.factory import build_reporting_service
from ..services.reporting.interfaces import ReportingService
from ..services.export.factory import build_export_service
from ..services.export.interfaces import EvidenceExportService


def get_runtime_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_case_repository(request: Request) -> Iterator[CaseRepository]:
    factory = cast(sessionmaker[Session], request.app.state.session_factory)
    with factory() as session:
        yield SqlAlchemyCaseRepository(session)


def get_analysis_orchestrator(request: Request) -> AnalysisOrchestrator:
    orchestrator = cast(
        AnalysisOrchestrator | None, request.app.state.analysis_orchestrator
    )
    if orchestrator is None:
        orchestrator = build_default_analysis_orchestrator(
            get_runtime_settings(request)
        )
        request.app.state.analysis_orchestrator = orchestrator
    return orchestrator


def get_reporting_service(request: Request) -> ReportingService:
    reporting = cast(ReportingService | None, request.app.state.reporting_service)
    if reporting is None:
        reporting = build_reporting_service()
        request.app.state.reporting_service = reporting
    return reporting


def get_export_service(request: Request) -> EvidenceExportService:
    export_svc = cast(EvidenceExportService | None, getattr(request.app.state, "export_service", None))
    if export_svc is None:
        export_svc = build_export_service()
        request.app.state.export_service = export_svc
    return export_svc

