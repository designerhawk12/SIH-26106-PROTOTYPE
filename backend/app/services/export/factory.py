"""Factory for building the export service."""

from .interfaces import EvidenceExportService
from .service import ZipEvidenceExportService


def build_export_service() -> EvidenceExportService:
    """Build and return the configured export service."""
    return ZipEvidenceExportService()
