"""Offline tests for the ipwho.is adapter."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from backend.app.schemas import GeoLocationStatus
from backend.app.services.geolocation import IpWhoIsProvider


@dataclass
class FakeResponse:
    status_code: int
    payload: Any

    def json(self) -> Any:
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeHTTPClient:
    def __init__(self, response: FakeResponse | Exception) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    async def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> FakeResponse:
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def successful_payload() -> dict[str, Any]:
    return {
        "success": True,
        "country": "United States",
        "country_code": "us",
        "region": "California",
        "city": "Mountain View",
        "latitude": 37.4056,
        "longitude": -122.0775,
        "connection": {
            "asn": 15169,
            "org": "Google LLC",
            "isp": "Google LLC",
            "route": "8.8.8.0/24",
        },
    }


def test_provider_success_normalizes_supported_fields() -> None:
    client = FakeHTTPClient(FakeResponse(200, successful_payload()))

    result = asyncio.run(IpWhoIsProvider(client=client).locate("8.8.8.8"))

    assert result.status is GeoLocationStatus.FOUND
    assert result.country == "United States"
    assert result.country_code == "US"
    assert result.region == "California"
    assert result.city == "Mountain View"
    assert result.isp == "Google LLC"
    assert result.organization == "Google LLC"
    assert result.asn == "AS15169"
    assert result.network == "8.8.8.0/24"
    assert result.latitude == 37.4056
    assert result.longitude == -122.0775
    assert result.provider == "ipwho.is"
    assert result.observed_infrastructure_only is True


def test_missing_city_coordinates_and_asn_remain_unknown_fields() -> None:
    payload = successful_payload()
    payload["city"] = None
    payload["latitude"] = None
    payload["longitude"] = None
    payload["connection"] = {"asn": None, "org": "Example Network", "isp": None}

    result = asyncio.run(
        IpWhoIsProvider(client=FakeHTTPClient(FakeResponse(200, payload))).locate("1.1.1.1")
    )

    assert result.status is GeoLocationStatus.FOUND
    assert result.city is None
    assert result.latitude is None
    assert result.longitude is None
    assert result.asn is None
    assert result.isp is None
    assert result.organization == "Example Network"


def test_ipv6_uses_encoded_provider_path() -> None:
    client = FakeHTTPClient(FakeResponse(200, successful_payload()))

    result = asyncio.run(
        IpWhoIsProvider(client=client).locate("2606:4700:4700::1111")
    )

    assert result.status is GeoLocationStatus.FOUND
    assert client.calls[0]["url"].endswith("/2606%3A4700%3A4700%3A%3A1111")


def test_timeout_and_network_failure_are_controlled_provider_errors() -> None:
    timeout = asyncio.run(
        IpWhoIsProvider(client=FakeHTTPClient(httpx.ReadTimeout("timeout"))).locate(
            "8.8.8.8"
        )
    )
    offline = asyncio.run(
        IpWhoIsProvider(client=FakeHTTPClient(httpx.ConnectError("offline"))).locate(
            "8.8.4.4"
        )
    )

    assert timeout.status is GeoLocationStatus.PROVIDER_ERROR
    assert offline.status is GeoLocationStatus.PROVIDER_ERROR


def test_not_found_and_malformed_responses_are_controlled() -> None:
    not_found = asyncio.run(
        IpWhoIsProvider(
            client=FakeHTTPClient(FakeResponse(200, {"success": False}))
        ).locate("8.8.8.8")
    )
    malformed = asyncio.run(
        IpWhoIsProvider(client=FakeHTTPClient(FakeResponse(200, {"success": True}))).locate(
            "8.8.4.4"
        )
    )

    assert not_found.status is GeoLocationStatus.NOT_FOUND
    assert malformed.status is GeoLocationStatus.FOUND
    assert malformed.country is None


def test_structurally_malformed_response_returns_provider_error() -> None:
    result = asyncio.run(
        IpWhoIsProvider(client=FakeHTTPClient(FakeResponse(200, ["unexpected"]))).locate(
            "8.8.8.8"
        )
    )

    assert result.status is GeoLocationStatus.PROVIDER_ERROR
