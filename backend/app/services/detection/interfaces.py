"""Threat-detection service boundary owned by Developer 3."""

from typing import Protocol, runtime_checkable

from ...schemas import DetectionResult, ParsedEmail


@runtime_checkable
class DetectionService(Protocol):
    """Treat all parsed email content as data, never as model instructions."""

    async def detect(self, parsed_email: ParsedEmail) -> DetectionResult:
        """Return explainable content findings without mutating evidence."""
        ...

