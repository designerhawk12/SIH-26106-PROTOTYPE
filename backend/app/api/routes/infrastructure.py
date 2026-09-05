"""Authenticated read-only access to persisted mail infrastructure."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from ...core import AppError
from ...db import CaseRepository
from ...schemas import Permission, UserProfile
from ...schemas.infrastructure import InfrastructureWorkspace
from ...services.orchestrator.infrastructure import aggregate_persisted_infrastructure
from ..dependencies import get_case_repository, require_permission

router = APIRouter(prefix="/api/v1/infrastructure", tags=["Infrastructure"])


@router.get("", response_model=InfrastructureWorkspace)
async def get_infrastructure(
    repository: Annotated[CaseRepository, Depends(get_case_repository)],
    _user: Annotated[UserProfile, Depends(require_permission(Permission.INSPECT_CASES))],
) -> InfrastructureWorkspace:
    try:
        analyses = await run_in_threadpool(repository.list_analyses)
        return await run_in_threadpool(aggregate_persisted_infrastructure, analyses)
    except Exception as exc:
        raise AppError(
            status_code=503, code="DATABASE_UNAVAILABLE",
            message="Persisted infrastructure is temporarily unavailable.",
        ) from exc
