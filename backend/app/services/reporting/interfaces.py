"""Forensic-reporting boundary owned by Developer 1."""

from typing import Protocol, runtime_checkable

from ...schemas import EmailAnalysis


@runtime_checkable
class ReportingService(Protocol):
    """Render a report from normalized evidence without active external content."""

    async def render_pdf(self, analysis: EmailAnalysis) -> bytes:
        """Return inert PDF bytes suitable for the report endpoint."""
        ...

