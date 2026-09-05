"""Pure persisted infrastructure projection. No network or service dependencies."""

from datetime import datetime, timezone
from ipaddress import ip_address
from math import isfinite

from ...schemas import EmailAnalysis, EnrichmentStatus, IOCType, ReputationVerdict
from ...schemas.infrastructure import (
    InfrastructureCase,
    InfrastructureObservation,
    InfrastructureRouteSegment,
    InfrastructureWorkspace,
)


def _public_ip(value: str | None) -> str | None:
    try:
        address = ip_address(value or "")
    except ValueError:
        return None
    if (
        not address.is_global or address.is_private or address.is_reserved
        or address.is_multicast or address.is_loopback or address.is_link_local
        or getattr(address, "scope_id", None)
    ):
        return None
    return str(address)


def _mappable(record: InfrastructureObservation) -> bool:
    location = record.location
    if location is None or location.status.value != "FOUND":
        return False
    lat, lon = location.latitude, location.longitude
    return (
        lat is not None and lon is not None
        and isfinite(lat) and isfinite(lon)
        and -90 <= lat <= 90 and -180 <= lon <= 180
        and (lat, lon) != (0, 0)
    )


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def aggregate_persisted_infrastructure(
    analyses: tuple[EmailAnalysis, ...],
) -> InfrastructureWorkspace:
    observations: list[InfrastructureObservation] = []
    segments: list[InfrastructureRouteSegment] = []
    for analysis in analyses:
        parsed = analysis.parsed_email
        observed = set()
        if parsed:
            observed.update(parsed.originating_public_ips)
            observed.update(
                ioc.normalized_value for ioc in parsed.iocs
                if ioc.type is IOCType.IP_ADDRESS
            )
            observed.update(hop.source_ip for hop in parsed.received_hops)
        observed.update(location.ip_address for location in analysis.geolocations)
        public_ips = sorted({ip for value in observed if (ip := _public_ip(value))})
        case = InfrastructureCase(
            case_id=analysis.case_id,
            subject=parsed.subject if parsed else None,
            status=analysis.status,
            risk_severity=analysis.risk.severity if analysis.risk else None,
        )
        by_ip: dict[str, list[InfrastructureObservation]] = {}
        for ip in public_ips:
            locations = [
                location for location in analysis.geolocations
                if _public_ip(location.ip_address) == ip
            ]
            findings = [
                finding for finding in (analysis.threat_intel.findings if analysis.threat_intel else ())
                if finding.indicator_type is IOCType.IP_ADDRESS
                and _public_ip(finding.indicator) == ip
            ]
            verdict = next((
                value for value in (
                    ReputationVerdict.MALICIOUS, ReputationVerdict.SUSPICIOUS,
                    ReputationVerdict.BENIGN, ReputationVerdict.UNKNOWN,
                ) if any(finding.verdict is value for finding in findings)
            ), ReputationVerdict.UNKNOWN)
            providers = tuple(sorted({finding.provider for finding in findings}))
            # Keep each case/provider observation intact, including conflicting or
            # simulated locations. Never merge fields into a fabricated location.
            for index, location in enumerate(locations or [None]):
                record = InfrastructureObservation(
                    id=f"{analysis.case_id}:{ip}:{index}",
                    ip_address=ip,
                    case=case,
                    observed_at=analysis.created_at,
                    location=location,
                    verdict=verdict,
                    threat_intel_status=(
                        analysis.threat_intel.status if analysis.threat_intel
                        else EnrichmentStatus.UNKNOWN
                    ),
                    threat_providers=providers,
                    demo=any("demo" in name.casefold() for name in (
                        *providers, location.provider or "" if location else "",
                    )),
                )
                observations.append(record)
                by_ip.setdefault(ip, []).append(record)
        if not parsed:
            continue
        # Received headers are newest first. Only adjacent, timestamp-supported
        # hops form segments; missing/ambiguous evidence breaks the route.
        hops = sorted(parsed.received_hops, key=lambda hop: hop.position, reverse=True)
        for earlier, later in zip(hops, hops[1:]):
            if (earlier.position != later.position + 1
                or earlier.timestamp is None or later.timestamp is None
                or _utc(earlier.timestamp) > _utc(later.timestamp)):
                continue
            start = by_ip.get(_public_ip(earlier.source_ip) or "", [])
            end = by_ip.get(_public_ip(later.source_ip) or "", [])
            if (len(start) != 1 or len(end) != 1 or start[0].id == end[0].id
                or not _mappable(start[0]) or not _mappable(end[0])):
                continue
            segments.append(InfrastructureRouteSegment(
                case_id=analysis.case_id,
                from_observation_id=start[0].id,
                to_observation_id=end[0].id,
                from_timestamp=earlier.timestamp,
                to_timestamp=later.timestamp,
            ))
    return InfrastructureWorkspace(
        observations=tuple(observations), route_segments=tuple(segments),
        cases_scanned=len(analyses),
    )
