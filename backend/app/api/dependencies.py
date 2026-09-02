"""FastAPI dependency adapters for infrastructure-owned components."""

from collections.abc import Iterator
from typing import cast

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from ..core import AppError, Settings
from ..db import CaseRepository, SqlAlchemyCaseRepository
from ..services.orchestrator.factory import build_default_analysis_orchestrator
from ..services.orchestrator.interfaces import AnalysisOrchestrator
from ..services.reporting.interfaces import ReportingService


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
        orchestrator = build_default_analysis_orchestrator()
        request.app.state.analysis_orchestrator = orchestrator
    return orchestrator


def get_reporting_service(request: Request) -> ReportingService:
    reporting = cast(ReportingService | None, request.app.state.reporting_service)
    if reporting is None:
        raise AppError(
            status_code=503,
            code="REPORTING_SERVICE_UNAVAILABLE",
            message="Reporting service is not configured.",
        )
    return reporting

