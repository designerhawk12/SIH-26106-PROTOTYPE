"""Validation and failure isolation for infrastructure geolocation."""

from __future__ import annotations

from collections.abc import Sequence
import ipaddress

from ...schemas import GeoLocationResult, GeoLocationStatus
from .providers import InfrastructureGeoProvider


FORENSIC_LIMITATION = (
    "Infrastructure geolocation describes observed network/mail-routing infrastructure "
    "and does not establish the physical location or identity of the attacker."
)


class ObservedInfrastructureGeoService:
    """Geolocate only validated global routing IPs; never perform attribution."""

    def __init__(self, provider: InfrastructureGeoProvider | None) -> None:
        self._provider = provider

    async def locate_public_ips(
        self, ip_addresses: Sequence[str]
    ) -> tuple[GeoLocationResult, ...]:
        results: list[GeoLocationResult] = []
        seen: set[str] = set()

        for supplied_value in ip_addresses:
            value = supplied_value.strip()
            try:
                parsed = ipaddress.ip_address(value)
            except ValueError:
                if value not in seen:
                    seen.add(value)
                    results.append(
                        GeoLocationResult(
                            ip_address=value,
                            status=GeoLocationStatus.UNKNOWN,
                        )
                    )
                continue

            normalized = parsed.compressed
            if normalized in seen:
                continue
            seen.add(normalized)

            if not parsed.is_global:
                results.append(
                    GeoLocationResult(
                        ip_address=normalized,
                        status=GeoLocationStatus.NOT_PUBLIC,
                    )
                )
                continue

            if self._provider is None:
                results.append(
                    GeoLocationResult(
                        ip_address=normalized,
                        status=GeoLocationStatus.PROVIDER_ERROR,
                    )
                )
                continue

            try:
                provider_result = await self._provider.locate(normalized)
            except Exception:  # noqa: BLE001 - provider isolation boundary
                provider_result = GeoLocationResult(
                    ip_address=normalized,
                    status=GeoLocationStatus.PROVIDER_ERROR,
                    provider=self._provider.name,
                )
            results.append(provider_result)

        return tuple(results)
