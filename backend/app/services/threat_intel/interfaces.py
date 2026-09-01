"""Threat-intelligence service boundary owned by Developer 4."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ...schemas import ExtractedIOC, ThreatIntelResult


@runtime_checkable
class ThreatIntelService(Protocol):
    """Enrich indicators without automatically browsing extracted URLs."""

    async def enrich(self, indicators: Sequence[ExtractedIOC]) -> ThreatIntelResult:
        """Return partial/unknown results on provider absence or failure."""
        ...

