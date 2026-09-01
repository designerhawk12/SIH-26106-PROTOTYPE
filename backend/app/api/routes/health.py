"""Health endpoint."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends

from ...core import Settings
from ...schemas import HealthResponse
from ..dependencies import get_runtime_settings

router = APIRouter(prefix="/api/v1", tags=["System"])


@router.get("/health", response_model=HealthResponse)
def health(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> HealthResponse:
    return HealthResponse(version=settings.app_version, timestamp=datetime.now(timezone.utc))

