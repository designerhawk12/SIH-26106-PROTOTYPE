"""Failure-contained aggregation of provider-neutral reputation lookups."""

from __future__ import annotations

from collections.abc import Sequence

from ...schemas import EnrichmentStatus, ExtractedIOC, ThreatIntelResult
from .providers import ProviderLookupResult, ProviderLookupStatus, ThreatIntelProvider


def _safe_error(provider: str, message: str | None) -> str:
    cleaned = " ".join((message or "Provider lookup failed.").split())
    return f"{provider}: {cleaned[:240]}"


class ThreatIntelEnrichmentService:
    """Enrich normalized IOCs without parsing messages or visiting indicators."""

    def __init__(self, providers: Sequence[ThreatIntelProvider]) -> None:
        self._providers = tuple(providers)

    async def enrich(self, indicators: Sequence[ExtractedIOC]) -> ThreatIntelResult:
        requested = tuple(indicators)
        if not requested:
            return ThreatIntelResult(
                status=EnrichmentStatus.COMPLETE,
                requested_indicators=(),
            )

        findings = []
        unknown = []
        errors: list[str] = []
        completed_lookup = False
        unknown_lookup = False
        failed_lookup = False

        for indicator in requested:
            capable = tuple(
                provider
                for provider in self._providers
                if indicator.type in provider.supported_types
            )
            if not capable:
                unknown.append(indicator)
                failed_lookup = True
                errors.append(f"No provider configured for {indicator.type.value} indicators.")
                continue

            indicator_has_finding = False
            for provider in capable:
                try:
                    result = await provider.lookup(indicator)
                except Exception:  # noqa: BLE001 - provider isolation boundary
                    result = ProviderLookupResult(
                        provider=provider.name,
                        indicator=indicator,
                        status=ProviderLookupStatus.ERROR,
                        error="Provider raised an unexpected error.",
                    )

                if result.status is ProviderLookupStatus.FOUND and result.finding is not None:
                    findings.append(result.finding)
                    indicator_has_finding = True
                    completed_lookup = True
                elif result.status is ProviderLookupStatus.NOT_FOUND:
                    completed_lookup = True
                elif result.status is ProviderLookupStatus.UNKNOWN:
                    unknown_lookup = True
                else:
                    failed_lookup = True
                    errors.append(_safe_error(result.provider, result.error))

            if not indicator_has_finding:
                unknown.append(indicator)

        if failed_lookup and not (completed_lookup or unknown_lookup):
            status = EnrichmentStatus.UNAVAILABLE
        elif failed_lookup:
            status = EnrichmentStatus.PARTIAL
        elif unknown_lookup and not completed_lookup:
            status = EnrichmentStatus.UNKNOWN
        else:
            status = EnrichmentStatus.COMPLETE

        return ThreatIntelResult(
            status=status,
            requested_indicators=requested,
            findings=tuple(findings),
            unknown_indicators=tuple(dict.fromkeys(unknown)),
            provider_errors=tuple(dict.fromkeys(errors)),
        )
