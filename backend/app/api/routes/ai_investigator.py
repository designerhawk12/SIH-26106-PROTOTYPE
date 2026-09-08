"""Authenticated, case-grounded AI investigator endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from ...core import AppError
from ...db import CaseRepository
from ...schemas import (
    AIAskRequest,
    AIInvestigationRequest,
    AIInvestigatorResponse,
    Permission,
    UserProfile,
)
from ...services.ai_investigator.interfaces import AIInvestigatorService
from ..dependencies import (
    get_ai_investigator_service,
    get_case_repository,
    require_permission,
)

router = APIRouter(prefix="/api/v1/cases", tags=["AI Investigator"])


async def _persisted_case(repository: CaseRepository, case_id: UUID):
    try:
        analysis = await run_in_threadpool(repository.get_analysis, case_id)
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="Case persistence is temporarily unavailable.",
        ) from exc
    if analysis is None:
        raise AppError(
            status_code=404,
            code="CASE_NOT_FOUND",
            message="The requested case was not found.",
        )
    return analysis


@router.post("/{case_id}/ai/investigate", response_model=AIInvestigatorResponse)
async def investigate_case(
    case_id: UUID,
    request: AIInvestigationRequest,
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    investigator: Annotated[
        AIInvestigatorService, Depends(get_ai_investigator_service)
    ],
    _user: Annotated[
        UserProfile, Depends(require_permission(Permission.INSPECT_CASES))
    ],
) -> AIInvestigatorResponse:
    analysis = await _persisted_case(repository, case_id)
    return await investigator.investigate(analysis, request.action)


@router.post("/{case_id}/ai/ask", response_model=AIInvestigatorResponse)
async def ask_about_case(
    case_id: UUID,
    request: AIAskRequest,
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    investigator: Annotated[
        AIInvestigatorService, Depends(get_ai_investigator_service)
    ],
    _user: Annotated[
        UserProfile, Depends(require_permission(Permission.INSPECT_CASES))
    ],
) -> AIInvestigatorResponse:
    analysis = await _persisted_case(repository, case_id)
    return await investigator.ask(analysis, request.question)
