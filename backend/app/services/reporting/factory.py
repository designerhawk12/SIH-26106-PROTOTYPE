"""Factory for building the reporting service."""

from .interfaces import ReportingService
from .service import ReportLabReportingService


def build_reporting_service() -> ReportingService:
    """Build and return the configured reporting service."""
    return ReportLabReportingService()
