"""Interfaces for evidence export service."""

from typing import Protocol

from ...schemas import EmailAnalysis


class EvidenceExportService(Protocol):
    """Interface for exporting structured forensic evidence."""

    async def export_case(self, analysis: EmailAnalysis) -> bytes:
        """
        Generate a ZIP archive of the available forensic evidence.
        
        Args:
            analysis: The complete persisted case analysis.
            
        Returns:
            bytes: The ZIP archive data.
        """
        ...
