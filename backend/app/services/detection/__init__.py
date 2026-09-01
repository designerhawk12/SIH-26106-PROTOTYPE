"""Offline threat-detection service and its contract."""

from .deterministic import DeterministicDetectionService, detect_email
from .interfaces import DetectionService

__all__ = ["DetectionService", "DeterministicDetectionService", "detect_email"]
