"""Offline HTTP-adapter tests; no live provider calls are made."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from backend.app.schemas import ExtractedIOC, IOCSource, IOCType, ReputationVerdict
from backend.app.services.threat_intel import (
    AbuseIPDBProvider,
    ProviderLookupStatus,
    VirusTotalProvider,
)


@dataclass
class FakeResponse:
    status_code: int
    payload: Any = None

    def json(self) -> Any:
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeHTTPClient:
    def __init__(self, response: FakeResponse | Exception) -> None:
        self.response = response
        self.get_calls: list[dict[str, Any]] = []
        self.upload_calls = 0

    async def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        params: Mapping[str, str | int] | None = None,
        timeout: float | None = None,
    ) -> FakeResponse:
        self.get_calls.append(
            {"url": url, "headers": headers, "params": params, "timeout": timeout}
        )
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

    async def post(self, *_args: object, **_kwargs: object) -> None:
        self.upload_calls += 1
        raise AssertionError("Attachment content must never be uploaded")


def ioc(ioc_type: IOCType, value: str) -> ExtractedIOC:
    return ExtractedIOC(
        type=ioc_type,
        value=value,
        normalized_value=value,
        source=(
            IOCSource.ATTACHMENT_METADATA
            if ioc_type is IOCType.ATTACHMENT_SHA256
            else IOCSource.BODY_TEXT
        ),
    )


def test_abuseipdb_malicious_and_clean_responses() -> None:
    malicious_client = FakeHTTPClient(
        FakeResponse(200, {"data": {"abuseConfidenceScore": 92, "totalReports": 20}})
    )
    clean_client = FakeHTTPClient(
        FakeResponse(200, {"data": {"abuseConfidenceScore": 0, "totalReports": 0}})
    )
    indicator = ioc(IOCType.IP_ADDRESS, "8.8.8.8")

    malicious = asyncio.run(AbuseIPDBProvider("secret", client=malicious_client).lookup(indicator))
    clean = asyncio.run(AbuseIPDBProvider("secret", client=clean_client).lookup(indicator))

    assert malicious.finding and malicious.finding.verdict is ReputationVerdict.MALICIOUS
    assert malicious.finding.provider == "AbuseIPDB"
    assert clean.finding and clean.finding.verdict is ReputationVerdict.BENIGN


def test_abuseipdb_missing_key_is_unavailable_without_http() -> None:
    client = FakeHTTPClient(AssertionError("HTTP must not be called"))

    result = asyncio.run(
        AbuseIPDBProvider(None, client=client).lookup(ioc(IOCType.IP_ADDRESS, "8.8.8.8"))
    )

    assert result.status is ProviderLookupStatus.UNAVAILABLE
    assert "key" in (result.error or "").lower()
    assert client.get_calls == []


def test_timeout_and_rate_limit_are_controlled_errors() -> None:
    indicator = ioc(IOCType.IP_ADDRESS, "8.8.4.4")
    timeout_client = FakeHTTPClient(httpx.ReadTimeout("timeout"))
    limited_client = FakeHTTPClient(FakeResponse(429, {}))

    timeout = asyncio.run(AbuseIPDBProvider("secret", client=timeout_client).lookup(indicator))
    limited = asyncio.run(AbuseIPDBProvider("secret", client=limited_client).lookup(indicator))

    assert timeout.status is ProviderLookupStatus.ERROR
    assert timeout.error == "Request timed out."
    assert limited.status is ProviderLookupStatus.ERROR
    assert "rate limit" in (limited.error or "").lower()


def test_network_unavailable_and_authentication_failure_are_controlled() -> None:
    indicator = ioc(IOCType.IP_ADDRESS, "8.8.8.8")
    network_client = FakeHTTPClient(httpx.ConnectError("offline"))
    forbidden_client = FakeHTTPClient(FakeResponse(403, {}))

    network = asyncio.run(
        AbuseIPDBProvider("secret", client=network_client).lookup(indicator)
    )
    forbidden = asyncio.run(
        AbuseIPDBProvider("secret", client=forbidden_client).lookup(indicator)
    )

    assert network.status is ProviderLookupStatus.ERROR
    assert network.error == "Network is unavailable."
    assert forbidden.status is ProviderLookupStatus.UNAVAILABLE
    assert "authentication" in (forbidden.error or "").lower()


def test_not_found_and_malformed_responses_are_not_benign() -> None:
    indicator = ioc(IOCType.IP_ADDRESS, "1.1.1.1")
    not_found = asyncio.run(
        AbuseIPDBProvider("secret", client=FakeHTTPClient(FakeResponse(404))).lookup(indicator)
    )
    malformed = asyncio.run(
        AbuseIPDBProvider("secret", client=FakeHTTPClient(FakeResponse(200, {"data": {}}))).lookup(
            indicator
        )
    )

    assert not_found.status is ProviderLookupStatus.NOT_FOUND
    assert not_found.finding is None
    assert malformed.status is ProviderLookupStatus.ERROR
    assert malformed.finding is None


def test_virustotal_domain_and_url_use_api_lookup_paths_only() -> None:
    payload = {
        "data": {
            "attributes": {
                "last_analysis_stats": {
                    "malicious": 1,
                    "suspicious": 0,
                    "harmless": 5,
                    "undetected": 4,
                },
                "categories": {"engine": "phishing"},
            }
        }
    }
    client = FakeHTTPClient(FakeResponse(200, payload))
    domain = ioc(IOCType.DOMAIN, "bad.example")
    url = ioc(IOCType.URL, "https://bad.example/login")
    provider = VirusTotalProvider("secret", client=client)

    domain_result = asyncio.run(provider.lookup(domain))
    url_result = asyncio.run(provider.lookup(url))

    assert domain_result.finding and domain_result.finding.provider == "VirusTotal"
    assert url_result.finding and url_result.finding.verdict is ReputationVerdict.MALICIOUS
    assert client.get_calls[0]["url"].endswith("/domains/bad.example")
    assert "https://bad.example/login" not in client.get_calls[1]["url"]


def test_hash_is_get_only_and_attachment_content_is_never_uploaded() -> None:
    digest = "a" * 64
    payload = {
        "data": {
            "attributes": {
                "last_analysis_stats": {
                    "malicious": 0,
                    "suspicious": 0,
                    "harmless": 12,
                    "undetected": 3,
                },
                "categories": {},
            }
        }
    }
    client = FakeHTTPClient(FakeResponse(200, payload))

    result = asyncio.run(
        VirusTotalProvider("secret", client=client).lookup(
            ioc(IOCType.ATTACHMENT_SHA256, digest)
        )
    )

    assert result.finding and result.finding.indicator == digest
    assert client.get_calls[0]["url"].endswith(f"/files/{digest}")
    assert client.upload_calls == 0
