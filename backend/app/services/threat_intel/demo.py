"""Explicit synthetic threat-intelligence provider for controlled demonstrations."""

from __future__ import annotations

from ...schemas import ExtractedIOC, IOCType, ReputationVerdict, ThreatFinding
from .providers import ProviderLookupResult, ProviderLookupStatus

DEMO_THREAT_INTEL_PROVIDER = "DEMO-SYNTHETIC (not live verified)"
_SUSPICIOUS_MARKERS = (
    "login",
    "verify",
    "credential",
    "account-update",
    "secure-portal",
)


class DemoThreatIntelProvider:
    """Return deterministic scenario data without network access or file uploads."""

    name = DEMO_THREAT_INTEL_PROVIDER
    supported_types = frozenset(
        {IOCType.IP_ADDRESS, IOCType.DOMAIN, IOCType.URL, IOCType.ATTACHMENT_SHA256}
    )

    async def lookup(self, indicator: ExtractedIOC) -> ProviderLookupResult:
        value = indicator.normalized_value.casefold()
        suspicious = indicator.type in {IOCType.DOMAIN, IOCType.URL} and any(
            marker in value for marker in _SUSPICIOUS_MARKERS
        )
        if not suspicious:
            return ProviderLookupResult(
                provider=self.name,
                indicator=indicator,
                status=ProviderLookupStatus.NOT_FOUND,
            )

        finding = ThreatFinding(
            indicator_type=indicator.type,
            indicator=indicator.normalized_value,
            provider=self.name,
            verdict=ReputationVerdict.SUSPICIOUS,
            confidence=0.5,
            categories=("synthetic-demo-scenario",),
            details=(
                "Synthetic demo fallback only; this finding was not returned by a live "
                "threat-intelligence provider."
            ),
        )
        return ProviderLookupResult(
            provider=self.name,
            indicator=indicator,
            status=ProviderLookupStatus.FOUND,
            finding=finding,
        )
