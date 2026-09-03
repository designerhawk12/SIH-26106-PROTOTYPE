"""Case persistence interface and SQLAlchemy implementation."""

from __future__ import annotations

import json
from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..schemas import EmailAnalysis
from .models import Case


class CaseRepository(Protocol):
    def create(self, analysis: EmailAnalysis) -> Case: ...

    def get(self, case_id: UUID) -> Case | None: ...

    def get_analysis(self, case_id: UUID) -> EmailAnalysis | None: ...

    def list(self, *, limit: int, offset: int) -> tuple[Case, ...]: ...

    def count(self) -> int: ...


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

