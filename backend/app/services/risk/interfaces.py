"""Deterministic risk-engine boundary owned by Developer 3."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ...schemas import (
    DetectionResult,
    GeoLocationResult,
    ParsedEmail,
    RiskResult,
    ThreatIntelResult,
)


@runtime_checkable
class RiskEngine(Protocol):
    """Produce a deterministic, versioned 0-100 score from normalized signals."""

    def score(
        self,
        *,
        parsed_email: ParsedEmail,
        detection: DetectionResult,
        threat_intel: ThreatIntelResult,
        geolocations: Sequence[GeoLocationResult],
    ) -> RiskResult:
        """Explain every score contribution and preserve unknown inputs."""
        ...

