"""Tests for provider-neutral enrichment aggregation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from backend.app.schemas import (
    EnrichmentStatus,
    ExtractedIOC,
    IOCSource,
    IOCType,
    ReputationVerdict,
    ThreatFinding,
)
from backend.app.services.threat_intel import (
    ProviderLookupResult,
    ProviderLookupStatus,
    ThreatIntelEnrichmentService,
)


def ioc(ioc_type: IOCType, value: str) -> ExtractedIOC:
    return ExtractedIOC(
        type=ioc_type,
        value=value,
        normalized_value=value,
        source=IOCSource.BODY_TEXT,
    )


@dataclass
class FakeProvider:
    name: str
    supported_types: frozenset[IOCType]
    status: ProviderLookupStatus
    verdict: ReputationVerdict = ReputationVerdict.UNKNOWN

    async def lookup(self, indicator: ExtractedIOC) -> ProviderLookupResult:
        finding = None
        if self.status is ProviderLookupStatus.FOUND:
            finding = ThreatFinding(
                indicator_type=indicator.type,
                indicator=indicator.normalized_value,
                provider=self.name,
                verdict=self.verdict,
                confidence=0.9,
            )
        return ProviderLookupResult(
            provider=self.name,
            indicator=indicator,
            status=self.status,
            finding=finding,
            error="controlled fake failure" if self.status is ProviderLookupStatus.ERROR else None,
        )


def test_malicious_ip_and_provider_identity_are_preserved() -> None:
    indicator = ioc(IOCType.IP_ADDRESS, "8.8.8.8")
    provider = FakeProvider(
        "MockAbuseDB",
        frozenset({IOCType.IP_ADDRESS}),
        ProviderLookupStatus.FOUND,
        ReputationVerdict.MALICIOUS,
    )

    result = asyncio.run(ThreatIntelEnrichmentService((provider,)).enrich((indicator,)))

    assert result.status is EnrichmentStatus.COMPLETE
    assert result.findings[0].verdict is ReputationVerdict.MALICIOUS
    assert result.findings[0].provider == "MockAbuseDB"


def test_not_found_remains_unknown_and_is_never_benign() -> None:
    indicator = ioc(IOCType.DOMAIN, "unknown.example")
    provider = FakeProvider(
        "MockDomainDB",
        frozenset({IOCType.DOMAIN}),
        ProviderLookupStatus.NOT_FOUND,
    )

    result = asyncio.run(ThreatIntelEnrichmentService((provider,)).enrich((indicator,)))

    assert result.status is EnrichmentStatus.COMPLETE
    assert result.findings == ()
    assert result.unknown_indicators == (indicator,)


def test_unavailable_provider_returns_controlled_unknown_result() -> None:
    indicator = ioc(IOCType.URL, "https://example.test/path")
    provider = FakeProvider(
        "MockURLDB",
        frozenset({IOCType.URL}),
        ProviderLookupStatus.ERROR,
    )

    result = asyncio.run(ThreatIntelEnrichmentService((provider,)).enrich((indicator,)))

    assert result.status is EnrichmentStatus.UNAVAILABLE
    assert result.unknown_indicators == (indicator,)
    assert result.provider_errors == ("MockURLDB: controlled fake failure",)


def test_domain_url_and_hash_iocs_are_dispatched_without_content() -> None:
    indicators = (
        ioc(IOCType.DOMAIN, "example.test"),
        ioc(IOCType.URL, "https://example.test/path"),
        ioc(IOCType.ATTACHMENT_SHA256, "a" * 64),
    )
    provider = FakeProvider(
        "MockMultiIOC",
        frozenset({IOCType.DOMAIN, IOCType.URL, IOCType.ATTACHMENT_SHA256}),
        ProviderLookupStatus.FOUND,
        ReputationVerdict.BENIGN,
    )

    result = asyncio.run(ThreatIntelEnrichmentService((provider,)).enrich(indicators))

    assert result.status is EnrichmentStatus.COMPLETE
    assert [finding.indicator_type for finding in result.findings] == [
        IOCType.DOMAIN,
        IOCType.URL,
        IOCType.ATTACHMENT_SHA256,
    ]
    assert all(finding.provider == "MockMultiIOC" for finding in result.findings)


def test_partial_status_when_one_provider_fails_and_another_completes() -> None:
    indicator = ioc(IOCType.IP_ADDRESS, "1.1.1.1")
    success = FakeProvider(
        "WorkingProvider",
        frozenset({IOCType.IP_ADDRESS}),
        ProviderLookupStatus.FOUND,
        ReputationVerdict.BENIGN,
    )
    failure = FakeProvider(
        "FailingProvider",
        frozenset({IOCType.IP_ADDRESS}),
        ProviderLookupStatus.ERROR,
    )

    result = asyncio.run(
        ThreatIntelEnrichmentService((success, failure)).enrich((indicator,))
    )

    assert result.status is EnrichmentStatus.PARTIAL
    assert result.findings[0].verdict is ReputationVerdict.BENIGN
    assert result.provider_errors[0].startswith("FailingProvider:")
