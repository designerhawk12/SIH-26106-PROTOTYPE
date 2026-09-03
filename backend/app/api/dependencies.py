"""FastAPI dependency adapters for infrastructure-owned components."""

from collections.abc import Callable, Iterator
from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from ..core import AppError, Settings
from ..db import (
    CaseRepository,
    SqlAlchemyCaseRepository,
    SqlAlchemyUserProfileRepository,
    UserProfileRepository,
)
from ..schemas import Permission, UserProfile
from ..services.auth import (
    IdentityProviderUnavailableError,
    IdentityVerifier,
    InvalidAccessTokenError,
    role_has_permission,
)
from ..services.auth.factory import build_identity_verifier
from ..services.orchestrator.factory import build_default_analysis_orchestrator
from ..services.orchestrator.interfaces import AnalysisOrchestrator
from ..services.reporting.factory import build_reporting_service
from ..services.reporting.interfaces import ReportingService
from ..services.export.factory import build_export_service
from ..services.export.interfaces import EvidenceExportService

bearer_scheme = HTTPBearer(auto_error=False)


def get_runtime_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_case_repository(request: Request) -> Iterator[CaseRepository]:
    factory = cast(sessionmaker[Session], request.app.state.session_factory)
    with factory() as session:
        yield SqlAlchemyCaseRepository(session)


def get_user_profile_repository(request: Request) -> Iterator[UserProfileRepository]:
    factory = cast(sessionmaker[Session], request.app.state.session_factory)
    with factory() as session:
        yield SqlAlchemyUserProfileRepository(session)


def get_identity_verifier(request: Request) -> IdentityVerifier:
    verifier = cast(IdentityVerifier | None, request.app.state.identity_verifier)
    if verifier is None:
        verifier = build_identity_verifier(get_runtime_settings(request))
        request.app.state.identity_verifier = verifier
    return verifier


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    verifier: Annotated[IdentityVerifier, Depends(get_identity_verifier)],
    profiles: Annotated[UserProfileRepository, Depends(get_user_profile_repository)],
) -> UserProfile:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise AppError(
            status_code=401,
            code="AUTHENTICATION_REQUIRED",
            message="A valid authenticated session is required.",
        )
    try:
        identity = await verifier.verify(credentials.credentials)
    except InvalidAccessTokenError as exc:
        raise AppError(
            status_code=401,
            code="INVALID_ACCESS_TOKEN",
            message="The authentication session is invalid or expired.",
        ) from exc
    except IdentityProviderUnavailableError as exc:
        raise AppError(
            status_code=503,
            code="AUTH_PROVIDER_UNAVAILABLE",
            message="Authentication is temporarily unavailable.",
        ) from exc

    try:
        return await run_in_threadpool(profiles.get_or_create, identity)
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="User profile persistence is temporarily unavailable.",
        ) from exc


def require_permission(permission: Permission) -> Callable[..., UserProfile]:
    async def authorize(
        current_user: Annotated[UserProfile, Depends(get_current_user)],
    ) -> UserProfile:
        if not role_has_permission(current_user.role, permission):
            raise AppError(
                status_code=403,
                code="INSUFFICIENT_PERMISSION",
                message="Your role does not permit this action.",
            )
        return current_user

    return authorize


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

