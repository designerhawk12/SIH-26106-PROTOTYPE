"""VirusTotal IOC adapter using reputation lookup endpoints only."""

from __future__ import annotations

import base64
import os
from typing import Any
from urllib.parse import quote

import httpx

from ...schemas import ExtractedIOC, IOCType, ReputationVerdict, ThreatFinding
from .providers import (
    AsyncHTTPClient,
    HTTPResponse,
    ProviderLookupResult,
    ProviderLookupStatus,
)


class VirusTotalProvider:
    name = "VirusTotal"
    supported_types = frozenset(
        {IOCType.IP_ADDRESS, IOCType.DOMAIN, IOCType.URL, IOCType.ATTACHMENT_SHA256}
    )
    _base_url = "https://www.virustotal.com/api/v3"

    def __init__(
        self,
        api_key: str | None,
        *,
        client: AsyncHTTPClient | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._api_key = api_key.strip() if api_key else None
        self._client = client
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_environment(
        cls,
        *,
        client: AsyncHTTPClient | None = None,
        timeout_seconds: float = 5.0,
    ) -> VirusTotalProvider:
        return cls(
            os.getenv("VIRUSTOTAL_API_KEY"),
            client=client,
            timeout_seconds=timeout_seconds,
        )

    def _lookup_path(self, indicator: ExtractedIOC) -> str | None:
        value = indicator.normalized_value
        if indicator.type is IOCType.IP_ADDRESS:
            return f"ip_addresses/{quote(value, safe='')}"
        if indicator.type is IOCType.DOMAIN:
            return f"domains/{quote(value, safe='')}"
        if indicator.type is IOCType.URL:
            url_id = base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")
            return f"urls/{url_id}"
        if indicator.type is IOCType.ATTACHMENT_SHA256:
            return f"files/{quote(value, safe='')}"
        return None

    async def _get(self, path: str) -> HTTPResponse:
        url = f"{self._base_url}/{path}"
        kwargs = {
            "headers": {"x-apikey": self._api_key or ""},
            "timeout": self._timeout_seconds,
        }
        if self._client is not None:
            return await self._client.get(url, **kwargs)
        async with httpx.AsyncClient() as client:
            return await client.get(url, **kwargs)

    async def lookup(self, indicator: ExtractedIOC) -> ProviderLookupResult:
        path = self._lookup_path(indicator)
        if path is None:
            return ProviderLookupResult(
                provider=self.name,
                indicator=indicator,
                status=ProviderLookupStatus.UNKNOWN,
            )
        if not self._api_key:
            return ProviderLookupResult(
                provider=self.name,
                indicator=indicator,
                status=ProviderLookupStatus.UNAVAILABLE,
                error="API key is not configured.",
            )

        try:
            response = await self._get(path)
        except httpx.TimeoutException:
            return self._error(indicator, "Request timed out.")
        except httpx.RequestError:
            return self._error(indicator, "Network is unavailable.")

        failure = self._http_failure(indicator, response.status_code)
        if failure:
            return failure
        try:
            payload = response.json()
            attributes = payload["data"]["attributes"]
            stats = attributes["last_analysis_stats"]
            malicious = self._count(stats, "malicious")
            suspicious = self._count(stats, "suspicious")
            harmless = self._count(stats, "harmless")
            undetected = self._count(stats, "undetected")
            categories_data = attributes.get("categories", {})
            if not isinstance(categories_data, dict):
                raise TypeError
        except (KeyError, TypeError, ValueError):
            return self._error(indicator, "Provider returned a malformed response.")

        total = malicious + suspicious + harmless + undetected
        if malicious:
            verdict = ReputationVerdict.MALICIOUS
            confidence = (malicious + suspicious) / total if total else None
        elif suspicious:
            verdict = ReputationVerdict.SUSPICIOUS
            confidence = suspicious / total if total else None
        elif harmless:
            verdict = ReputationVerdict.BENIGN
            confidence = harmless / total if total else None
        else:
            verdict = ReputationVerdict.UNKNOWN
            confidence = None

        finding = ThreatFinding(
            indicator_type=indicator.type,
            indicator=indicator.normalized_value,
            provider=self.name,
            verdict=verdict,
            confidence=confidence,
            categories=tuple(dict.fromkeys(str(value) for value in categories_data.values())),
            details=(
                f"Engine results: malicious={malicious}, suspicious={suspicious}, "
                f"harmless={harmless}, undetected={undetected}."
            ),
        )
        return ProviderLookupResult(
            provider=self.name,
            indicator=indicator,
            status=ProviderLookupStatus.FOUND,
            finding=finding,
        )

    @staticmethod
    def _count(stats: dict[str, Any], name: str) -> int:
        value = stats.get(name, 0)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise TypeError
        return value

    def _http_failure(
        self, indicator: ExtractedIOC, status_code: int
    ) -> ProviderLookupResult | None:
        if status_code == 404:
            return ProviderLookupResult(
                provider=self.name,
                indicator=indicator,
                status=ProviderLookupStatus.NOT_FOUND,
            )
        if status_code in {401, 403}:
            return ProviderLookupResult(
                provider=self.name,
                indicator=indicator,
                status=ProviderLookupStatus.UNAVAILABLE,
                error="Provider rejected authentication.",
            )
        if status_code == 429:
            return self._error(indicator, "Provider rate limit exceeded.")
        if not 200 <= status_code < 300:
            return self._error(indicator, f"Provider returned HTTP {status_code}.")
        return None

    def _error(self, indicator: ExtractedIOC, message: str) -> ProviderLookupResult:
        return ProviderLookupResult(
            provider=self.name,
            indicator=indicator,
            status=ProviderLookupStatus.ERROR,
            error=message,
        )
