"""Canonical dependency ports consumed by the infrastructure orchestrator."""

from ..detection.interfaces import DetectionService as ThreatDetectionService
from ..email_forensics.interfaces import EmailForensicsService
from ..geolocation.interfaces import GeoLocationService
from ..reporting.interfaces import ReportingService
from ..risk.interfaces import RiskEngine as RiskService
from ..threat_intel.interfaces import ThreatIntelService

__all__ = [
    "EmailForensicsService",
    "GeoLocationService",
    "ReportingService",
    "RiskService",
    "ThreatDetectionService",
    "ThreatIntelService",
]
