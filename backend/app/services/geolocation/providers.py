"""Provider boundary for observed mail-routing infrastructure lookups."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from ...schemas import GeoLocationResult


@runtime_checkable
class InfrastructureGeoProvider(Protocol):
    name: str

    async def locate(self, ip_address: str) -> GeoLocationResult:
        """Locate a prevalidated, globally routable infrastructure address."""
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
        timeout: float | None = None,
    ) -> HTTPResponse:
        ...
