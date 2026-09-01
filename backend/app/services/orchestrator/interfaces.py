"""Analysis-orchestration boundary owned by Developer 1."""

from typing import Protocol, runtime_checkable

from ...schemas import EmailAnalysis


@runtime_checkable
class AnalysisOrchestrator(Protocol):
    """Coordinate isolated analysis services and contain optional-provider failures."""

    async def analyze(
        self, raw_email: bytes, *, original_filename: str | None = None
    ) -> EmailAnalysis:
        """Analyze a validated upload and return a persisted case contract."""
        ...

