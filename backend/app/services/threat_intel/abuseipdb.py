"""AbuseIPDB IP-reputation adapter."""

from __future__ import annotations

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


class AbuseIPDBProvider:
    name = "AbuseIPDB"
    supported_types = frozenset({IOCType.IP_ADDRESS})
    _endpoint = "https://api.abuseipdb.com/api/v2/check"

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
    ) -> AbuseIPDBProvider:
        return cls(
            os.getenv("ABUSEIPDB_API_KEY"),
            client=client,
            timeout_seconds=timeout_seconds,
        )

    async def _get(self, indicator: ExtractedIOC) -> HTTPResponse:
        kwargs = {
            "headers": {"Key": self._api_key or "", "Accept": "application/json"},
            "params": {"ipAddress": indicator.normalized_value, "maxAgeInDays": 90},
            "timeout": self._timeout_seconds,
        }
        if self._client is not None:
            return await self._client.get(self._endpoint, **kwargs)
        async with httpx.AsyncClient() as client:
            return await client.get(self._endpoint, **kwargs)

    async def lookup(self, indicator: ExtractedIOC) -> ProviderLookupResult:
        if indicator.type is not IOCType.IP_ADDRESS:
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
            response = await self._get(indicator)
        except httpx.TimeoutException:
            return self._error(indicator, "Request timed out.")
        except httpx.RequestError:
            return self._error(indicator, "Network is unavailable.")

        failure = self._http_failure(indicator, response.status_code)
        if failure:
            return failure
        try:
            payload = response.json()
            data = payload["data"]
            score = data["abuseConfidenceScore"]
            reports = data.get("totalReports", 0)
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                raise TypeError
            if not isinstance(reports, int) or isinstance(reports, bool):
                raise TypeError
        except (KeyError, TypeError, ValueError):
            return self._error(indicator, "Provider returned a malformed response.")

        bounded_score = max(0.0, min(100.0, float(score)))
        if bounded_score >= 70:
            verdict = ReputationVerdict.MALICIOUS
        elif bounded_score > 0:
            verdict = ReputationVerdict.SUSPICIOUS
        else:
            verdict = ReputationVerdict.BENIGN
        finding = ThreatFinding(
            indicator_type=indicator.type,
            indicator=indicator.normalized_value,
            provider=self.name,
            verdict=verdict,
            confidence=bounded_score / 100,
            categories=("reported-abuse",) if reports else (),
            reference=(
                "https://www.abuseipdb.com/check/"
                f"{quote(indicator.normalized_value, safe='')}"
            ),
            details=f"Abuse confidence score {bounded_score:g}/100; total reports {reports}.",
        )
        return ProviderLookupResult(
            provider=self.name,
            indicator=indicator,
            status=ProviderLookupStatus.FOUND,
            finding=finding,
        )

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
