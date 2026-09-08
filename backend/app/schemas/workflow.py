"""Contracts for analyst-authored workflow records, separate from forensic evidence."""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from .email import ContractModel
from .enums import IOCType


class AuditAction(StrEnum):
    CASE_ANALYZED = "CASE_ANALYZED"
    REPORT_GENERATED = "REPORT_GENERATED"
    EVIDENCE_EXPORTED = "EVIDENCE_EXPORTED"
    NOTE_ADDED = "NOTE_ADDED"
    NOTE_UPDATED = "NOTE_UPDATED"
    NOTE_DELETED = "NOTE_DELETED"
    IOC_WATCHLISTED = "IOC_WATCHLISTED"
    IOC_UNWATCHLISTED = "IOC_UNWATCHLISTED"
    ROLE_CHANGED = "ROLE_CHANGED"


class CreateAnalystNoteRequest(ContractModel):
    content: str = Field(min_length=1, max_length=5_000)

    @field_validator("content")
    @classmethod
    def require_non_blank_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Note content must not be blank.")
        return normalized


class UpdateAnalystNoteRequest(CreateAnalystNoteRequest):
    pass


class AnalystNote(ContractModel):
    note_id: UUID
    case_id: UUID
    author_user_id: UUID
    author_display_name: str
    content: str
    created_at: datetime
    updated_at: datetime


class AnalystNoteListResponse(ContractModel):
    items: tuple[AnalystNote, ...] = ()


class AuditEvent(ContractModel):
    event_id: UUID
    actor_user_id: UUID | None = None
    action: AuditAction
    resource_type: str
    resource_id: str
    timestamp: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEventListResponse(ContractModel):
    items: tuple[AuditEvent, ...] = ()


class CreateWatchlistRequest(ContractModel):
    ioc_type: IOCType
    value: str = Field(min_length=1, max_length=2_048)
    reason: str | None = Field(default=None, max_length=1_000)

    @field_validator("ioc_type", mode="before")
    @classmethod
    def allow_watchable_iocs_only(cls, value: object) -> IOCType:
        parsed = IOCType(value) if isinstance(value, str) else value
        if not isinstance(parsed, IOCType):
            raise ValueError("IOC type must be valid.")
        if parsed not in {
            IOCType.IP_ADDRESS,
            IOCType.DOMAIN,
            IOCType.URL,
            IOCType.ATTACHMENT_SHA256,
        }:
            raise ValueError("Only IP, domain, URL, and attachment hash IOCs can be watched.")
        return parsed

    @field_validator("value")
    @classmethod
    def require_non_blank_indicator(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("IOC value must not be blank.")
        return normalized


class WatchlistEntry(ContractModel):
    watchlist_id: UUID
    ioc_type: IOCType
    value: str
    created_by_user_id: UUID
    created_by_display_name: str
    reason: str | None = None
    created_at: datetime


class WatchlistResponse(ContractModel):
    items: tuple[WatchlistEntry, ...] = ()
