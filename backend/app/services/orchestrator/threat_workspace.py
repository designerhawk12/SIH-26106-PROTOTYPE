"""Aggregate only persisted intelligence; this module never invokes providers."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...schemas import (
    EmailAnalysis,
    EnrichmentStatus,
    GeoLocationStatus,
    IntelligenceStatus,
    IOCType,
    ProviderStatusRecord,
    ProviderWorkspaceStatus,
    ReputationVerdict,
    ThreatCaseReference,
    ThreatIntelligenceWorkspace,
    ThreatIOCRecord,
    ThreatSummary,
)

SUPPORTED_IOCS = {
    IOCType.IP_ADDRESS,
    IOCType.DOMAIN,
    IOCType.URL,
    IOCType.ATTACHMENT_SHA256,
}
DEMO_MARKER = "demo-synthetic"


def _is_demo_provider(name: str) -> bool:
    return DEMO_MARKER in name.casefold()


@dataclass
class _MutableIOC:
    ioc_type: IOCType
    value: str
    statuses: list[IntelligenceStatus] = field(default_factory=list)
    providers: set[str] = field(default_factory=set)
    confidences: list[float] = field(default_factory=list)
    categories: set[str] = field(default_factory=set)
    details: set[str] = field(default_factory=set)
    filenames: set[str] = field(default_factory=set)
    cases: dict[str, ThreatCaseReference] = field(default_factory=dict)


@dataclass
class _MutableProvider:
    name: str
    category: str
    states: list[ProviderWorkspaceStatus] = field(default_factory=list)
    messages: set[str] = field(default_factory=set)


def _status_for_verdict(verdict: ReputationVerdict) -> IntelligenceStatus:
    return IntelligenceStatus(verdict.value)


def _final_ioc_status(statuses: list[IntelligenceStatus]) -> IntelligenceStatus:
    for status in (
        IntelligenceStatus.MALICIOUS,
        IntelligenceStatus.SUSPICIOUS,
        IntelligenceStatus.BENIGN,
        IntelligenceStatus.UNAVAILABLE,
        IntelligenceStatus.UNKNOWN,
    ):
        if status in statuses:
            return status
    return IntelligenceStatus.UNKNOWN


def _final_provider_status(
    states: list[ProviderWorkspaceStatus],
) -> ProviderWorkspaceStatus:
    if not states:
        return ProviderWorkspaceStatus.UNKNOWN
    unique = set(states)
    if ProviderWorkspaceStatus.AVAILABLE in unique and (
        ProviderWorkspaceStatus.UNAVAILABLE in unique
        or ProviderWorkspaceStatus.PARTIAL in unique
    ):
        return ProviderWorkspaceStatus.PARTIAL
    if ProviderWorkspaceStatus.AVAILABLE in unique:
        return ProviderWorkspaceStatus.AVAILABLE
    if ProviderWorkspaceStatus.PARTIAL in unique:
        return ProviderWorkspaceStatus.PARTIAL
    if ProviderWorkspaceStatus.UNAVAILABLE in unique:
        return ProviderWorkspaceStatus.UNAVAILABLE
    return ProviderWorkspaceStatus.UNKNOWN


def _provider(
    providers: dict[tuple[str, str], _MutableProvider],
    name: str,
    category: str,
) -> _MutableProvider:
    return providers.setdefault((category, name), _MutableProvider(name, category))


def aggregate_persisted_threat_intelligence(
    analyses: tuple[EmailAnalysis, ...],
) -> ThreatIntelligenceWorkspace:
    """Build a cross-case view from normalized persisted results only."""

    records: dict[tuple[IOCType, str], _MutableIOC] = {}
    providers: dict[tuple[str, str], _MutableProvider] = {}
    _provider(providers, "AbuseIPDB", "THREAT_INTELLIGENCE")
    _provider(providers, "VirusTotal", "THREAT_INTELLIGENCE")
    _provider(providers, "ipwho.is", "GEOLOCATION")

    for analysis in analyses:
        parsed = analysis.parsed_email
        if parsed is None:
            continue
        case = ThreatCaseReference(
            case_id=analysis.case_id,
            subject=parsed.subject,
            original_filename=analysis.original_filename,
        )
        attachments = {item.sha256: item for item in parsed.attachments}
        observed = {
            (ioc.type, ioc.normalized_value): ioc
            for ioc in parsed.iocs
            if ioc.type in SUPPORTED_IOCS
        }
        for attachment in parsed.attachments:
            observed.setdefault((IOCType.ATTACHMENT_SHA256, attachment.sha256), None)

        findings = {
            (finding.indicator_type, finding.indicator): finding
            for finding in (
                analysis.threat_intel.findings if analysis.threat_intel else ()
            )
        }
        unavailable = (
            analysis.threat_intel is not None
            and analysis.threat_intel.status is EnrichmentStatus.UNAVAILABLE
        )

        for key in observed:
            ioc_type, value = key
            record = records.setdefault(
                key, _MutableIOC(ioc_type=ioc_type, value=value)
            )
            record.cases[str(analysis.case_id)] = case
            attachment = attachments.get(value)
            if attachment and attachment.filename:
                record.filenames.add(attachment.filename)
            finding = findings.get(key)
            if finding is None:
                record.statuses.append(
                    IntelligenceStatus.UNAVAILABLE
                    if unavailable
                    else IntelligenceStatus.UNKNOWN
                )
                continue
            record.statuses.append(_status_for_verdict(finding.verdict))
            record.providers.add(finding.provider)
            if finding.confidence is not None:
                record.confidences.append(finding.confidence)
            record.categories.update(finding.categories)
            if finding.details:
                record.details.add(finding.details)
            _provider(
                providers, finding.provider, "THREAT_INTELLIGENCE"
            ).states.append(ProviderWorkspaceStatus.AVAILABLE)

        threat_intel = analysis.threat_intel
        if threat_intel is not None:
            demo_analysis = any(
                _is_demo_provider(finding.provider)
                for finding in threat_intel.findings
            ) or any("demo mode" in warning.casefold() for warning in analysis.warnings)
            if demo_analysis:
                _provider(
                    providers,
                    "DEMO-SYNTHETIC (not live verified)",
                    "THREAT_INTELLIGENCE",
                ).states.append(ProviderWorkspaceStatus.AVAILABLE)
            elif threat_intel.status is EnrichmentStatus.COMPLETE:
                attempted = set()
                if any(key[0] is IOCType.IP_ADDRESS for key in observed):
                    attempted.add("AbuseIPDB")
                if any(
                    key[0] in {IOCType.DOMAIN, IOCType.URL, IOCType.ATTACHMENT_SHA256}
                    for key in observed
                ):
                    attempted.add("VirusTotal")
                for name in attempted:
                    _provider(providers, name, "THREAT_INTELLIGENCE").states.append(
                        ProviderWorkspaceStatus.AVAILABLE
                    )
            elif threat_intel.status is EnrichmentStatus.UNAVAILABLE:
                for name in ("AbuseIPDB", "VirusTotal"):
                    _provider(providers, name, "THREAT_INTELLIGENCE").states.append(
                        ProviderWorkspaceStatus.UNAVAILABLE
                    )
            elif threat_intel.status is EnrichmentStatus.PARTIAL and not demo_analysis:
                for name in ("AbuseIPDB", "VirusTotal"):
                    _provider(providers, name, "THREAT_INTELLIGENCE").states.append(
                        ProviderWorkspaceStatus.PARTIAL
                    )
            for message in threat_intel.provider_errors:
                matched = False
                for name in ("AbuseIPDB", "VirusTotal"):
                    if name.casefold() in message.casefold():
                        provider = _provider(providers, name, "THREAT_INTELLIGENCE")
                        provider.states.append(ProviderWorkspaceStatus.UNAVAILABLE)
                        provider.messages.add(message)
                        matched = True
                if not matched:
                    for name in ("AbuseIPDB", "VirusTotal"):
                        _provider(providers, name, "THREAT_INTELLIGENCE").messages.add(
                            message
                        )

        for location in analysis.geolocations:
            name = location.provider or "ipwho.is"
            provider = _provider(providers, name, "GEOLOCATION")
            if location.status in {
                GeoLocationStatus.FOUND,
                GeoLocationStatus.NOT_FOUND,
            }:
                provider.states.append(ProviderWorkspaceStatus.AVAILABLE)
            elif location.status is GeoLocationStatus.PROVIDER_ERROR:
                provider.states.append(ProviderWorkspaceStatus.UNAVAILABLE)
            else:
                provider.states.append(ProviderWorkspaceStatus.UNKNOWN)

    indicators = tuple(
        ThreatIOCRecord(
            ioc_type=record.ioc_type,
            value=record.value,
            status=_final_ioc_status(record.statuses),
            providers=tuple(sorted(record.providers)),
            confidence=max(record.confidences) if record.confidences else None,
            categories=tuple(sorted(record.categories)),
            details=tuple(sorted(record.details)),
            filename=sorted(record.filenames)[0] if record.filenames else None,
            associated_cases=tuple(record.cases.values()),
            demo=any(_is_demo_provider(name) for name in record.providers),
        )
        for _, record in sorted(
            records.items(), key=lambda item: (item[0][0], item[0][1])
        )
    )
    statuses = [record.status for record in indicators]
    provider_rows = tuple(
        ProviderStatusRecord(
            name=provider.name,
            category=provider.category,
            status=_final_provider_status(provider.states),
            demo=_is_demo_provider(provider.name),
            messages=tuple(sorted(provider.messages)),
        )
        for _, provider in sorted(providers.items())
    )
    return ThreatIntelligenceWorkspace(
        summary=ThreatSummary(
            total_observed_iocs=len(indicators),
            suspicious_or_malicious=sum(
                status
                in {
                    IntelligenceStatus.SUSPICIOUS,
                    IntelligenceStatus.MALICIOUS,
                }
                for status in statuses
            ),
            benign=statuses.count(IntelligenceStatus.BENIGN),
            unknown=statuses.count(IntelligenceStatus.UNKNOWN),
            unavailable=statuses.count(IntelligenceStatus.UNAVAILABLE),
        ),
        indicators=indicators,
        providers=provider_rows,
        cases_scanned=len(analyses),
    )
