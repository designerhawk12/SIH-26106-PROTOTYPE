"""Tests for validation and provider failure containment."""

from __future__ import annotations

import asyncio

from backend.app.schemas import GeoLocationResult, GeoLocationStatus
from backend.app.services.geolocation import ObservedInfrastructureGeoService


class RecordingProvider:
    name = "recording-geo"

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[str] = []

    async def locate(self, ip_address: str) -> GeoLocationResult:
        self.calls.append(ip_address)
        if self.fail:
            raise RuntimeError("controlled provider outage")
        return GeoLocationResult(
            ip_address=ip_address,
            status=GeoLocationStatus.FOUND,
            country="United States",
            provider=self.name,
        )


def test_valid_public_ipv4_and_ipv6_are_normalized_and_dispatched() -> None:
    provider = RecordingProvider()
    service = ObservedInfrastructureGeoService(provider)

    results = asyncio.run(
        service.locate_public_ips((" 8.8.8.8 ", "2606:4700:4700:0000:0000:0000:0000:1111"))
    )

    assert [result.ip_address for result in results] == [
        "8.8.8.8",
        "2606:4700:4700::1111",
    ]
    assert provider.calls == ["8.8.8.8", "2606:4700:4700::1111"]
    assert all(result.observed_infrastructure_only for result in results)


def test_private_loopback_link_local_reserved_and_invalid_ips_are_not_dispatched() -> None:
    provider = RecordingProvider()
    service = ObservedInfrastructureGeoService(provider)

    results = asyncio.run(
        service.locate_public_ips(
            (
                "10.0.0.1",
                "127.0.0.1",
                "169.254.1.1",
                "192.0.2.1",
                "not-an-ip",
            )
        )
    )

    assert provider.calls == []
    assert [result.status for result in results[:4]] == [GeoLocationStatus.NOT_PUBLIC] * 4
    assert results[4].status is GeoLocationStatus.UNKNOWN


def test_unavailable_provider_returns_controlled_results() -> None:
    no_provider = ObservedInfrastructureGeoService(None)
    failing_provider = RecordingProvider(fail=True)

    missing = asyncio.run(no_provider.locate_public_ips(("8.8.8.8",)))
    failed = asyncio.run(
        ObservedInfrastructureGeoService(failing_provider).locate_public_ips(("1.1.1.1",))
    )

    assert missing[0].status is GeoLocationStatus.PROVIDER_ERROR
    assert failed[0].status is GeoLocationStatus.PROVIDER_ERROR
    assert failed[0].provider == "recording-geo"


def test_duplicate_normalized_addresses_are_looked_up_once() -> None:
    provider = RecordingProvider()

    results = asyncio.run(
        ObservedInfrastructureGeoService(provider).locate_public_ips(
            ("2606:4700:4700::1111", "2606:4700:4700:0:0:0:0:1111")
        )
    )

    assert len(results) == 1
    assert provider.calls == ["2606:4700:4700::1111"]
