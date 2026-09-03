"""Authenticated profile and administrator role-management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from ...core import AppError
from ...db import UserProfileRepository
from ...schemas import (
    Permission,
    UpdateProfileRequest,
    UpdateRoleRequest,
    UserListResponse,
    UserProfile,
)
from ..dependencies import (
    get_current_user,
    get_user_profile_repository,
    require_permission,
)

router = APIRouter(prefix="/api/v1", tags=["Authentication"])


@router.get("/auth/me", response_model=UserProfile)
async def current_user(
    profile: Annotated[UserProfile, Depends(get_current_user)],
) -> UserProfile:
    return profile


@router.patch("/auth/me", response_model=UserProfile)
async def update_current_user(
    update: UpdateProfileRequest,
    profile: Annotated[UserProfile, Depends(get_current_user)],
    repository: Annotated[
        UserProfileRepository, Depends(get_user_profile_repository)
    ],
) -> UserProfile:
    try:
        updated = await run_in_threadpool(
            repository.update_profile, profile.user_id, update
        )
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="User profile persistence is temporarily unavailable.",
        ) from exc
    if updated is None:
        raise AppError(status_code=404, code="PROFILE_NOT_FOUND", message="Profile not found.")
    return updated


@router.get("/admin/users", response_model=UserListResponse)
async def list_users(
    _admin: Annotated[
        UserProfile, Depends(require_permission(Permission.MANAGE_USERS))
    ],
    repository: Annotated[
        UserProfileRepository, Depends(get_user_profile_repository)
    ],
) -> UserListResponse:
    try:
        users = await run_in_threadpool(repository.list)
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="User profile persistence is temporarily unavailable.",
        ) from exc
    return UserListResponse(items=users)


@router.patch("/admin/users/{user_id}/role", response_model=UserProfile)
async def update_user_role(
    user_id: UUID,
    update: UpdateRoleRequest,
    _admin: Annotated[
        UserProfile, Depends(require_permission(Permission.MANAGE_USERS))
    ],
    repository: Annotated[
        UserProfileRepository, Depends(get_user_profile_repository)
    ],
) -> UserProfile:
    try:
        updated = await run_in_threadpool(repository.update_role, user_id, update.role)
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="User profile persistence is temporarily unavailable.",
        ) from exc
    if updated is None:
        raise AppError(status_code=404, code="PROFILE_NOT_FOUND", message="Profile not found.")
    return updated
