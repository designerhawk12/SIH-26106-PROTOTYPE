"""Authenticated analyst workflow endpoints, kept separate from forensic evidence."""

from __future__ import annotations

import ipaddress
from typing import Annotated
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from starlette.concurrency import run_in_threadpool

from ...core import AppError
from ...db import CaseRepository, WorkflowRepository
from ...schemas import (
    AnalystNote,
    AnalystNoteListResponse,
    AuditAction,
    AuditEventListResponse,
    CreateAnalystNoteRequest,
    CreateWatchlistRequest,
    IOCType,
    Permission,
    UpdateAnalystNoteRequest,
    UserProfile,
    UserRole,
    WatchlistEntry,
    WatchlistResponse,
)
from ..dependencies import (
    get_case_repository,
    get_current_user,
    get_workflow_repository,
    require_permission,
)

cases_router = APIRouter(prefix="/api/v1/cases", tags=["Analyst Workflow"])
watchlist_router = APIRouter(prefix="/api/v1/watchlist", tags=["IOC Watchlist"])


async def _database(operation, *args, **kwargs):  # type: ignore[no-untyped-def]
    try:
        return await run_in_threadpool(operation, *args, **kwargs)
    except Exception as exc:
        raise AppError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="Analyst workflow persistence is temporarily unavailable.",
        ) from exc


async def _require_case(repository: CaseRepository, case_id: UUID) -> None:
    if await _database(repository.get, case_id) is None:
        raise AppError(status_code=404, code="CASE_NOT_FOUND", message="The requested case was not found.")


def _canonical_ioc(ioc_type: IOCType, value: str) -> str | None:
    candidate = value.strip()
    if ioc_type is IOCType.IP_ADDRESS:
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            return None
    if ioc_type is IOCType.DOMAIN:
        domain = candidate.strip(".[](){}<>,;:\"'").lower()
        try:
            return domain.encode("idna").decode("ascii") if domain and " " not in domain else None
        except UnicodeError:
            return None
    if ioc_type is IOCType.URL:
        try:
            parsed = urlsplit(candidate)
        except ValueError:
            return None
        if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
            return None
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return None
        port = f":{parsed.port}" if parsed.port else ""
        return urlunsplit((parsed.scheme.lower(), f"{hostname}{port}", parsed.path, parsed.query, ""))
    if ioc_type is IOCType.ATTACHMENT_SHA256:
        normalized = candidate.lower()
        return normalized if len(normalized) == 64 and all(char in "0123456789abcdef" for char in normalized) else None
    return None


async def _persisted_ioc_value(
    repository: CaseRepository, request: CreateWatchlistRequest
) -> str:
    canonical = _canonical_ioc(request.ioc_type, request.value)
    if canonical is None:
        raise AppError(status_code=422, code="INVALID_IOC", message="The IOC value is not valid for its type.")
    for analysis in await _database(repository.list_analyses):
        parsed = analysis.parsed_email
        if parsed is None:
            continue
        observed = [(ioc.type, ioc.normalized_value) for ioc in parsed.iocs]
        observed.extend((IOCType.ATTACHMENT_SHA256, item.sha256) for item in parsed.attachments)
        for ioc_type, value in observed:
            if ioc_type is request.ioc_type and _canonical_ioc(ioc_type, value) == canonical:
                return value
    raise AppError(
        status_code=404,
        code="IOC_NOT_OBSERVED",
        message="Only indicators already observed in persisted cases can be watched.",
    )


def _can_modify_note(note: AnalystNote, user: UserProfile) -> bool:
    return note.author_user_id == user.user_id or user.role is UserRole.ADMIN


@cases_router.get("/{case_id}/notes", response_model=AnalystNoteListResponse)
async def list_notes(
    case_id: UUID,
    cases: Annotated[CaseRepository, Depends(get_case_repository)],
    workflow: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
    _user: Annotated[UserProfile, Depends(require_permission(Permission.INSPECT_CASES))],
) -> AnalystNoteListResponse:
    await _require_case(cases, case_id)
    return AnalystNoteListResponse(items=await _database(workflow.list_notes, case_id))


@cases_router.post("/{case_id}/notes", response_model=AnalystNote, status_code=status.HTTP_201_CREATED)
async def create_note(
    case_id: UUID,
    request: CreateAnalystNoteRequest,
    cases: Annotated[CaseRepository, Depends(get_case_repository)],
    workflow: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
    user: Annotated[UserProfile, Depends(require_permission(Permission.CREATE_ANALYST_NOTES))],
) -> AnalystNote:
    await _require_case(cases, case_id)
    note = await _database(workflow.create_note, case_id, user, request)
    await _database(
        workflow.record_audit,
        actor_user_id=user.user_id,
        action=AuditAction.NOTE_ADDED,
        resource_type="CASE",
        resource_id=str(case_id),
        metadata={"note_id": str(note.note_id)},
    )
    return note


@cases_router.patch("/{case_id}/notes/{note_id}", response_model=AnalystNote)
async def update_note(
    case_id: UUID,
    note_id: UUID,
    request: UpdateAnalystNoteRequest,
    cases: Annotated[CaseRepository, Depends(get_case_repository)],
    workflow: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
    user: Annotated[UserProfile, Depends(require_permission(Permission.CREATE_ANALYST_NOTES))],
) -> AnalystNote:
    await _require_case(cases, case_id)
    notes = await _database(workflow.list_notes, case_id)
    existing = next((note for note in notes if note.note_id == note_id), None)
    if existing is None:
        raise AppError(status_code=404, code="NOTE_NOT_FOUND", message="The analyst note was not found.")
    if not _can_modify_note(existing, user):
        raise AppError(status_code=403, code="NOTE_MODIFICATION_FORBIDDEN", message="You may edit only your own analyst notes.")
    updated = await _database(workflow.update_note, note_id, request)
    if updated is None:
        raise AppError(status_code=404, code="NOTE_NOT_FOUND", message="The analyst note was not found.")
    await _database(
        workflow.record_audit,
        actor_user_id=user.user_id,
        action=AuditAction.NOTE_UPDATED,
        resource_type="CASE",
        resource_id=str(case_id),
        metadata={"note_id": str(note_id)},
    )
    return updated


@cases_router.delete(
    "/{case_id}/notes/{note_id}",
    status_code=status.HTTP_200_OK,
    response_class=Response,
    response_model=None,
)
async def delete_note(
    case_id: UUID,
    note_id: UUID,
    cases: Annotated[CaseRepository, Depends(get_case_repository)],
    workflow: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
    user: Annotated[UserProfile, Depends(require_permission(Permission.CREATE_ANALYST_NOTES))],
) -> None:
    await _require_case(cases, case_id)
    notes = await _database(workflow.list_notes, case_id)
    existing = next((note for note in notes if note.note_id == note_id), None)
    if existing is None:
        raise AppError(status_code=404, code="NOTE_NOT_FOUND", message="The analyst note was not found.")
    if not _can_modify_note(existing, user):
        raise AppError(status_code=403, code="NOTE_MODIFICATION_FORBIDDEN", message="You may delete only your own analyst notes.")
    await _database(workflow.delete_note, note_id)
    await _database(
        workflow.record_audit,
        actor_user_id=user.user_id,
        action=AuditAction.NOTE_DELETED,
        resource_type="CASE",
        resource_id=str(case_id),
        metadata={"note_id": str(note_id)},
    )


@cases_router.get("/{case_id}/audit", response_model=AuditEventListResponse)
async def list_case_audit(
    case_id: UUID,
    cases: Annotated[CaseRepository, Depends(get_case_repository)],
    workflow: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
    _user: Annotated[UserProfile, Depends(require_permission(Permission.INSPECT_CASES))],
) -> AuditEventListResponse:
    await _require_case(cases, case_id)
    return AuditEventListResponse(items=await _database(workflow.list_audit, case_id))


@watchlist_router.get("", response_model=WatchlistResponse)
async def list_watchlist(
    workflow: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
    _user: Annotated[UserProfile, Depends(require_permission(Permission.INSPECT_CASES))],
) -> WatchlistResponse:
    return WatchlistResponse(items=await _database(workflow.list_watchlist))


@watchlist_router.post("", response_model=WatchlistEntry, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    request: CreateWatchlistRequest,
    cases: Annotated[CaseRepository, Depends(get_case_repository)],
    workflow: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
    user: Annotated[UserProfile, Depends(require_permission(Permission.MANAGE_IOC_WATCHLIST))],
) -> WatchlistEntry:
    value = await _persisted_ioc_value(cases, request)
    if await _database(workflow.get_watchlist, request.ioc_type, value) is not None:
        raise AppError(status_code=409, code="IOC_ALREADY_WATCHLISTED", message="This IOC is already on the watchlist.")
    entry = await _database(workflow.create_watchlist, request, user, value)
    await _database(
        workflow.record_audit,
        actor_user_id=user.user_id,
        action=AuditAction.IOC_WATCHLISTED,
        resource_type="IOC",
        resource_id=f"{entry.ioc_type.value}:{entry.value}",
        metadata={"watchlist_id": str(entry.watchlist_id), "ioc_type": entry.ioc_type.value},
    )
    return entry


@watchlist_router.delete(
    "/{watchlist_id}",
    status_code=status.HTTP_200_OK,
    response_class=Response,
    response_model=None,
)
async def delete_watchlist(
    watchlist_id: UUID,
    workflow: Annotated[WorkflowRepository, Depends(get_workflow_repository)],
    user: Annotated[UserProfile, Depends(require_permission(Permission.MANAGE_IOC_WATCHLIST))],
) -> None:
    entries = await _database(workflow.list_watchlist)
    existing = next((entry for entry in entries if entry.watchlist_id == watchlist_id), None)
    if existing is None:
        raise AppError(status_code=404, code="WATCHLIST_ENTRY_NOT_FOUND", message="The watchlist entry was not found.")
    if existing.created_by_user_id != user.user_id and user.role is not UserRole.ADMIN:
        raise AppError(status_code=403, code="WATCHLIST_MODIFICATION_FORBIDDEN", message="You may remove only your own watchlist entries.")
    await _database(workflow.delete_watchlist, watchlist_id)
    await _database(
        workflow.record_audit,
        actor_user_id=user.user_id,
        action=AuditAction.IOC_UNWATCHLISTED,
        resource_type="IOC",
        resource_id=f"{existing.ioc_type.value}:{existing.value}",
        metadata={"watchlist_id": str(watchlist_id), "ioc_type": existing.ioc_type.value},
    )
