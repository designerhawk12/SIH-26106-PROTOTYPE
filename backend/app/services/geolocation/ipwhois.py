"""ipwho.is adapter for observed infrastructure geolocation."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from ...schemas import GeoLocationResult, GeoLocationStatus
from .providers import AsyncHTTPClient, HTTPResponse


class IpWhoIsProvider:
    name = "ipwho.is"
    _base_url = "https://ipwho.is"

    def __init__(
        self,
        *,
        client: AsyncHTTPClient | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def _get(self, ip_address: str) -> HTTPResponse:
        url = f"{self._base_url}/{quote(ip_address, safe='')}"
        kwargs = {
            "headers": {"Accept": "application/json"},
            "timeout": self._timeout_seconds,
        }
        if self._client is not None:
            return await self._client.get(url, **kwargs)
        async with httpx.AsyncClient() as client:
            return await client.get(url, **kwargs)

    async def locate(self, ip_address: str) -> GeoLocationResult:
        try:
            response = await self._get(ip_address)
        except (httpx.TimeoutException, httpx.RequestError):
            return self._provider_error(ip_address)

        if response.status_code == 404:
            return GeoLocationResult(
                ip_address=ip_address,
                status=GeoLocationStatus.NOT_FOUND,
                provider=self.name,
            )
        if not 200 <= response.status_code < 300:
            return self._provider_error(ip_address)

        try:
            payload = response.json()
            if not isinstance(payload, dict):
                raise TypeError
            success = payload.get("success")
            if success is False:
                return GeoLocationResult(
                    ip_address=ip_address,
                    status=GeoLocationStatus.NOT_FOUND,
                    provider=self.name,
                )
            if success is not True:
                raise TypeError
            connection = payload.get("connection") or {}
            if not isinstance(connection, dict):
                raise TypeError
            latitude = self._coordinate(payload.get("latitude"), -90, 90)
            longitude = self._coordinate(payload.get("longitude"), -180, 180)
            asn = self._asn(connection.get("asn"))
            result = GeoLocationResult(
                ip_address=ip_address,
                status=GeoLocationStatus.FOUND,
                country=self._text(payload.get("country")),
                country_code=self._country_code(payload.get("country_code")),
                city=self._text(payload.get("city")),
                region=self._text(payload.get("region")),
                isp=self._text(connection.get("isp")),
                asn=asn,
                organization=self._text(connection.get("org")),
                network=self._text(connection.get("route")),
                latitude=latitude,
                longitude=longitude,
                provider=self.name,
                observed_infrastructure_only=True,
            )
        except (TypeError, ValueError):
            return self._provider_error(ip_address)
        return result

    def _provider_error(self, ip_address: str) -> GeoLocationResult:
        return GeoLocationResult(
            ip_address=ip_address,
            status=GeoLocationStatus.PROVIDER_ERROR,
            provider=self.name,
        )

    @staticmethod
    def _text(value: Any) -> str | None:
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            raise TypeError
        return value.strip() or None

    @staticmethod
    def _country_code(value: Any) -> str | None:
        text = IpWhoIsProvider._text(value)
        return text.upper() if text else None

    @staticmethod
    def _coordinate(value: Any, minimum: float, maximum: float) -> float | None:
        if value is None:
            return None
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError
        coordinate = float(value)
        if not minimum <= coordinate <= maximum:
            raise ValueError
        return coordinate

    @staticmethod
    def _asn(value: Any) -> str | None:
        if value is None or value == "":
            return None
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise TypeError
        text = str(value).strip().upper()
        if not text:
            return None
        return text if text.startswith("AS") else f"AS{text}"
