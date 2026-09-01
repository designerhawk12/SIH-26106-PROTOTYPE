"""Infrastructure-geolocation service boundary owned by Developer 4."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ...schemas import GeoLocationResult


@runtime_checkable
class GeoLocationService(Protocol):
    """Locate observed public routing infrastructure, not people or attackers."""

    async def locate_public_ips(
        self, ip_addresses: Sequence[str]
    ) -> tuple[GeoLocationResult, ...]:
        """Return one explicit result per requested address where practical."""
        ...

