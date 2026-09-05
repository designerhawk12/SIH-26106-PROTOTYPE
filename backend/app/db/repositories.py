"""Case persistence interface and SQLAlchemy implementation."""

from __future__ import annotations

import json
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..schemas import EmailAnalysis, UpdateProfileRequest, UserProfile, UserRole
from ..services.auth.interfaces import AuthenticatedIdentity
from ..services.auth.rbac import permissions_for_role
from .models import Case, UserProfileRecord


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

