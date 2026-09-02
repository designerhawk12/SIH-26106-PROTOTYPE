"""Forensic-reporting contracts."""

from .factory import build_reporting_service
from .interfaces import ReportingService

__all__ = ["ReportingService", "build_reporting_service"]
