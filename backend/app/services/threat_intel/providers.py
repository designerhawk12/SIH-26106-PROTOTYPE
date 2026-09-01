"""Narrow provider contracts used by threat-intelligence adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping, Protocol, runtime_checkable

from ...schemas import ExtractedIOC, IOCType, ThreatFinding


class ProviderLookupStatus(StrEnum):
    """Internal provider outcome; normalized into existing shared contracts."""

    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class ProviderLookupResult:
    provider: str
    indicator: ExtractedIOC
    status: ProviderLookupStatus
    finding: ThreatFinding | None = None
    error: str | None = None


@runtime_checkable
class ThreatIntelProvider(Protocol):
    name: str
    supported_types: frozenset[IOCType]

    async def lookup(self, indicator: ExtractedIOC) -> ProviderLookupResult:
        """Look up only the supplied normalized IOC; never fetch the IOC itself."""
        ...


class HTTPResponse(Protocol):
    status_code: int

    def json(self) -> Any:
        ...


class AsyncHTTPClient(Protocol):
    async def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, str | int] | None = None,
        timeout: float | None = None,
    ) -> HTTPResponse:
        ...
