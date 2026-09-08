"""Forensic-reporting boundary owned by Developer 1."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ...schemas import AnalystNote, EmailAnalysis


@runtime_checkable
class ReportingService(Protocol):
    """Render a report from normalized evidence without active external content."""

    async def render_pdf(
        self,
        analysis: EmailAnalysis,
        *,
        analyst_notes: Sequence[AnalystNote] = (),
    ) -> bytes:
        """Return inert PDF bytes from persisted evidence and notes only."""
        ...
