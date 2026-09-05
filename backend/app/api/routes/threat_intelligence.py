"""Read-only persisted threat-intelligence workspace endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from ...core import AppError
from ...db import CaseRepository
from ...schemas import Permission, ThreatIntelligenceWorkspace, UserProfile
from ...services.orchestrator.threat_workspace import (
    aggregate_persisted_threat_intelligence,
)
from ..dependencies import get_case_repository, require_permission

router = APIRouter(prefix="/api/v1/threat-intelligence", tags=["Threat Intelligence"])


@router.get("", response_model=ThreatIntelligenceWorkspace)
async def get_threat_intelligence_workspace(
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    _user: Annotated[
        UserProfile, Depends(require_permission(Permission.INSPECT_CASES))
    ],
) -> ThreatIntelligenceWorkspace:
    try:
        analyses = await run_in_threadpool(repository.list_analyses)
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="Persisted threat intelligence is temporarily unavailable.",
        ) from exc
    return aggregate_persisted_threat_intelligence(analyses)

