"""Read-only, sanitized system configuration endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ...core import Settings
from ...schemas import Permission, SystemStatusResponse, UserProfile
from ...services.system_status import build_system_status
from ..dependencies import get_runtime_settings, require_permission

router = APIRouter(prefix="/api/v1/system", tags=["System"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    _admin: Annotated[
        UserProfile, Depends(require_permission(Permission.VIEW_SYSTEM_CONFIGURATION))
    ],
) -> SystemStatusResponse:
    """Return safe configuration state for administrators, never secret values."""

    return build_system_status(settings)
