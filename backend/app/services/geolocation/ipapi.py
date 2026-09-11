"""ip-api.com provider for observed mail-infrastructure geolocation."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from ...schemas import GeoLocationResult, GeoLocationStatus


class IpApiProvider:
    """Look up validated public infrastructure IPs using ip-api.com."""

    name = "ip-api.com"
    _base_url = "http://ip-api.com/json"

    def __init__(
        self,
        *,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._timeout_seconds = timeout_seconds

    async def locate(
        self,
        ip_address: str,
    ) -> GeoLocationResult:
        url = (
            f"{self._base_url}/"
            f"{quote(ip_address, safe='')}"
        )

        params = {
            "fields": (
                "status,message,country,countryCode,region,city,"
                "lat,lon,isp,as,org,query"
            )
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers={"Accept": "application/json"},
                    timeout=self._timeout_seconds,
                )
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

            status = payload.get("status")

            if status == "fail":
                return GeoLocationResult(
                    ip_address=ip_address,
                    status=GeoLocationStatus.NOT_FOUND,
                    provider=self.name,
                )

            if status != "success":
                raise TypeError

            latitude = self._coordinate(
                payload.get("lat"),
                -90,
                90,
            )

            longitude = self._coordinate(
                payload.get("lon"),
                -180,
                180,
            )

            asn = self._asn(payload.get("as"))

            return GeoLocationResult(
                ip_address=ip_address,
                status=GeoLocationStatus.FOUND,
                country=self._text(
                    payload.get("country")
                ),
                country_code=self._country_code(
                    payload.get("countryCode")
                ),
                city=self._text(
                    payload.get("city")
                ),
                region=self._text(
                    payload.get("region")
                ),
                isp=self._text(
                    payload.get("isp")
                ),
                asn=asn,
                organization=self._text(
                    payload.get("org")
                ),
                network=None,
                latitude=latitude,
                longitude=longitude,
                provider=self.name,
                observed_infrastructure_only=True,
            )

        except (TypeError, ValueError):
            return self._provider_error(ip_address)

    def _provider_error(
        self,
        ip_address: str,
    ) -> GeoLocationResult:
        return GeoLocationResult(
            ip_address=ip_address,
            status=GeoLocationStatus.PROVIDER_ERROR,
            provider=self.name,
        )

    @staticmethod
    def _text(
        value: Any,
    ) -> str | None:
        if value is None or value == "":
            return None

        if not isinstance(value, str):
            raise TypeError

        text = value.strip()

        return text or None

    @staticmethod
    def _country_code(
        value: Any,
    ) -> str | None:
        text = IpApiProvider._text(value)

        return text.upper() if text else None

    @staticmethod
    def _coordinate(
        value: Any,
        minimum: float,
        maximum: float,
    ) -> float | None:
        if value is None:
            return None

        if isinstance(value, bool):
            raise TypeError

        if not isinstance(value, (int, float)):
            raise TypeError

        coordinate = float(value)

        if not minimum <= coordinate <= maximum:
            raise ValueError

        return coordinate

    @staticmethod
    def _asn(
        value: Any,
    ) -> str | None:
        if value is None or value == "":
            return None

        if isinstance(value, bool):
            raise TypeError

        if not isinstance(value, (str, int)):
            raise TypeError

        text = str(value).strip().upper()

        if not text:
            return None

        return text if text.startswith("AS") else f"AS{text}"