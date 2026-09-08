"""Case persistence interface and SQLAlchemy implementation."""

from __future__ import annotations

import json
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..schemas import (
    AnalystNote,
    AuditAction,
    AuditEvent,
    CreateAnalystNoteRequest,
    CreateWatchlistRequest,
    EmailAnalysis,
    IOCType,
    UpdateAnalystNoteRequest,
    UpdateProfileRequest,
    UserProfile,
    UserRole,
    WatchlistEntry,
)
from ..services.auth.interfaces import AuthenticatedIdentity
from ..services.auth.rbac import permissions_for_role
from .models import (
    AnalystNoteRecord,
    AuditEventRecord,
    Case,
    IOCWatchlistRecord,
    UserProfileRecord,
)


class CaseRepository(Protocol):
    def create(self, analysis: EmailAnalysis) -> Case: ...

    def get(self, case_id: UUID) -> Case | None: ...

    def get_analysis(self, case_id: UUID) -> EmailAnalysis | None: ...

    def list(self, *, limit: int, offset: int) -> tuple[Case, ...]: ...

    def count(self) -> int: ...

    def list_analyses(self) -> tuple[EmailAnalysis, ...]: ...


class SqlAlchemyCaseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, analysis: EmailAnalysis) -> Case:
        row = Case(
            id=analysis.case_id,
            created_at=analysis.created_at,
            updated_at=analysis.completed_at or analysis.created_at,
            status=analysis.status.value,
            filename=analysis.original_filename or "unnamed.eml",
            email_sha256=(
                analysis.parsed_email.original_sha256
                if analysis.parsed_email is not None
                else None
            ),
            risk_score=analysis.risk.score if analysis.risk is not None else None,
            severity=(
                analysis.risk.severity.value if analysis.risk is not None else None
            ),
            analysis_json=analysis.model_dump(mode="json"),
        )
        self._session.add(row)
        try:
            self._session.commit()
            self._session.refresh(row)
        except SQLAlchemyError:
            self._session.rollback()
            raise
        return row

    def get(self, case_id: UUID) -> Case | None:
        return self._session.get(Case, case_id)

    def get_analysis(self, case_id: UUID) -> EmailAnalysis | None:
        row = self.get(case_id)
        if row is None:
            return None
        return EmailAnalysis.model_validate_json(json.dumps(row.analysis_json))

    def list(self, *, limit: int, offset: int) -> tuple[Case, ...]:
        statement = (
            select(Case).order_by(Case.created_at.desc()).limit(limit).offset(offset)
        )
        return tuple(self._session.scalars(statement).all())

    def count(self) -> int:
        return int(self._session.scalar(select(func.count()).select_from(Case)) or 0)

    def list_analyses(self) -> tuple[EmailAnalysis, ...]:
        statement = select(Case.analysis_json).order_by(Case.created_at.desc())
        return tuple(
            EmailAnalysis.model_validate_json(json.dumps(payload))
            for payload in self._session.scalars(statement)
        )


class UserProfileRepository(Protocol):
    def get_or_create(self, identity: AuthenticatedIdentity) -> UserProfile: ...

    def get(self, user_id: UUID) -> UserProfile | None: ...

    def list(self) -> tuple[UserProfile, ...]: ...

    def update_profile(
        self, user_id: UUID, update: UpdateProfileRequest
    ) -> UserProfile | None: ...

    def update_role(self, user_id: UUID, role: UserRole) -> UserProfile | None: ...


def _metadata_text(metadata: dict[str, Any], *keys: str, limit: int) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:limit]
    return None


def _profile_schema(row: UserProfileRecord) -> UserProfile:
    role = UserRole(row.role)
    return UserProfile(
        user_id=row.user_id,
        display_name=row.display_name,
        email=row.email,
        organization=row.organization,
        role=role,
        permissions=permissions_for_role(role),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyUserProfileRepository:
    """Store authorization roles separately from user-editable Auth metadata."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create(self, identity: AuthenticatedIdentity) -> UserProfile:
        existing = self._session.get(UserProfileRecord, identity.user_id)
        if existing is not None:
            if existing.email != identity.email:
                existing.email = identity.email
                self._commit()
            return _profile_schema(existing)

        display_name = _metadata_text(
            identity.user_metadata, "display_name", "full_name", "name", limit=120
        ) or identity.email.split("@", 1)[0][:120]
        organization = _metadata_text(
            identity.user_metadata, "organization", "team", limit=160
        )
        row = UserProfileRecord(
            user_id=identity.user_id,
            display_name=display_name,
            email=identity.email,
            organization=organization,
            role=UserRole.ANALYST.value,
        )
        self._session.add(row)
        try:
            self._session.commit()
            self._session.refresh(row)
        except IntegrityError:
            self._session.rollback()
            concurrent = self._session.get(UserProfileRecord, identity.user_id)
            if concurrent is None:
                raise
            row = concurrent
        except SQLAlchemyError:
            self._session.rollback()
            raise
        return _profile_schema(row)

    def get(self, user_id: UUID) -> UserProfile | None:
        row = self._session.get(UserProfileRecord, user_id)
        return _profile_schema(row) if row is not None else None

    def list(self) -> tuple[UserProfile, ...]:
        statement = select(UserProfileRecord).order_by(
            UserProfileRecord.created_at.asc()
        )
        return tuple(_profile_schema(row) for row in self._session.scalars(statement))

    def update_profile(
        self, user_id: UUID, update: UpdateProfileRequest
    ) -> UserProfile | None:
        row = self._session.get(UserProfileRecord, user_id)
        if row is None:
            return None
        if update.display_name is not None:
            row.display_name = update.display_name.strip()
        if update.organization is not None:
            row.organization = update.organization.strip() or None
        self._commit()
        return _profile_schema(row)

    def update_role(self, user_id: UUID, role: UserRole) -> UserProfile | None:
        row = self._session.get(UserProfileRecord, user_id)
        if row is None:
            return None
        row.role = role.value
        self._commit()
        return _profile_schema(row)

    def _commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise


class WorkflowRepository(Protocol):
    def list_notes(self, case_id: UUID) -> tuple[AnalystNote, ...]: ...

    def create_note(
        self, case_id: UUID, author: UserProfile, request: CreateAnalystNoteRequest
    ) -> AnalystNote: ...

    def update_note(
        self, note_id: UUID, request: UpdateAnalystNoteRequest
    ) -> AnalystNote | None: ...

    def delete_note(self, note_id: UUID) -> AnalystNote | None: ...

    def list_audit(self, case_id: UUID) -> tuple[AuditEvent, ...]: ...

    def record_audit(
        self,
        *,
        actor_user_id: UUID | None,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent: ...

    def list_watchlist(self) -> tuple[WatchlistEntry, ...]: ...

    def get_watchlist(self, ioc_type: IOCType, value: str) -> WatchlistEntry | None: ...

    def create_watchlist(
        self, request: CreateWatchlistRequest, author: UserProfile, value: str
    ) -> WatchlistEntry: ...

    def delete_watchlist(self, watchlist_id: UUID) -> WatchlistEntry | None: ...


_SENSITIVE_METADATA_MARKERS = frozenset(
    {"authorization", "password", "secret", "token", "api_key", "database_url"}
)


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Persist compact intentional metadata only; request objects are never accepted here."""

    safe: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        key_text = str(key)[:80]
        if any(marker in key_text.casefold() for marker in _SENSITIVE_METADATA_MARKERS):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key_text] = value[:500] if isinstance(value, str) else value
    return safe


def _note_schema(row: AnalystNoteRecord) -> AnalystNote:
    return AnalystNote(
        note_id=row.id,
        case_id=row.case_id,
        author_user_id=row.author_user_id,
        author_display_name=row.author_display_name,
        content=row.content,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _audit_schema(row: AuditEventRecord) -> AuditEvent:
    return AuditEvent(
        event_id=row.id,
        actor_user_id=row.actor_user_id,
        action=AuditAction(row.action),
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        timestamp=row.timestamp,
        metadata=_safe_metadata(row.metadata_json),
    )


def _watchlist_schema(row: IOCWatchlistRecord) -> WatchlistEntry:
    return WatchlistEntry(
        watchlist_id=row.id,
        ioc_type=IOCType(row.ioc_type),
        value=row.normalized_value,
        created_by_user_id=row.created_by_user_id,
        created_by_display_name=row.created_by_display_name,
        reason=row.reason,
        created_at=row.created_at,
    )


class SqlAlchemyWorkflowRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_notes(self, case_id: UUID) -> tuple[AnalystNote, ...]:
        statement = select(AnalystNoteRecord).where(AnalystNoteRecord.case_id == case_id).order_by(AnalystNoteRecord.created_at.asc())
        return tuple(_note_schema(row) for row in self._session.scalars(statement))

    def create_note(
        self, case_id: UUID, author: UserProfile, request: CreateAnalystNoteRequest
    ) -> AnalystNote:
        row = AnalystNoteRecord(
            case_id=case_id,
            author_user_id=author.user_id,
            author_display_name=author.display_name,
            content=request.content,
        )
        self._session.add(row)
        self._commit()
        self._session.refresh(row)
        return _note_schema(row)

    def update_note(
        self, note_id: UUID, request: UpdateAnalystNoteRequest
    ) -> AnalystNote | None:
        row = self._session.get(AnalystNoteRecord, note_id)
        if row is None:
            return None
        row.content = request.content
        self._commit()
        self._session.refresh(row)
        return _note_schema(row)

    def delete_note(self, note_id: UUID) -> AnalystNote | None:
        row = self._session.get(AnalystNoteRecord, note_id)
        if row is None:
            return None
        schema = _note_schema(row)
        self._session.delete(row)
        self._commit()
        return schema

    def list_audit(self, case_id: UUID) -> tuple[AuditEvent, ...]:
        statement = select(AuditEventRecord).where(
            AuditEventRecord.resource_type == "CASE",
            AuditEventRecord.resource_id == str(case_id),
        ).order_by(AuditEventRecord.timestamp.desc())
        return tuple(_audit_schema(row) for row in self._session.scalars(statement))

    def record_audit(
        self,
        *,
        actor_user_id: UUID | None,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        row = AuditEventRecord(
            actor_user_id=actor_user_id,
            action=action.value,
            resource_type=resource_type[:48],
            resource_id=resource_id[:128],
            metadata_json=_safe_metadata(metadata),
        )
        self._session.add(row)
        self._commit()
        self._session.refresh(row)
        return _audit_schema(row)

    def list_watchlist(self) -> tuple[WatchlistEntry, ...]:
        statement = select(IOCWatchlistRecord).order_by(IOCWatchlistRecord.created_at.desc())
        return tuple(_watchlist_schema(row) for row in self._session.scalars(statement))

    def get_watchlist(self, ioc_type: IOCType, value: str) -> WatchlistEntry | None:
        statement = select(IOCWatchlistRecord).where(
            IOCWatchlistRecord.ioc_type == ioc_type.value,
            IOCWatchlistRecord.normalized_value == value,
        )
        row = self._session.scalar(statement)
        return _watchlist_schema(row) if row is not None else None

    def create_watchlist(
        self, request: CreateWatchlistRequest, author: UserProfile, value: str
    ) -> WatchlistEntry:
        row = IOCWatchlistRecord(
            ioc_type=request.ioc_type.value,
            normalized_value=value,
            created_by_user_id=author.user_id,
            created_by_display_name=author.display_name,
            reason=request.reason.strip() if request.reason else None,
        )
        self._session.add(row)
        self._commit()
        self._session.refresh(row)
        return _watchlist_schema(row)

    def delete_watchlist(self, watchlist_id: UUID) -> WatchlistEntry | None:
        row = self._session.get(IOCWatchlistRecord, watchlist_id)
        if row is None:
            return None
        schema = _watchlist_schema(row)
        self._session.delete(row)
        self._commit()
        return schema

    def _commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise

