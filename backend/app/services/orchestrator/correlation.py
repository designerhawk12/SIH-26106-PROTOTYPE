"""Deterministic correlation of normalized evidence already stored in cases.

This module deliberately has no provider, network, LLM, or database dependency.
It compares only ``EmailAnalysis`` values supplied by the persistence layer.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from ...schemas import (
    CorrelationIndicatorType,
    CorrelationStrength,
    EmailAnalysis,
    IOCType,
    RelatedCase,
    RelatedCasesResponse,
    SharedIndicator,
)

_SUBJECT_PREFIX = re.compile(r"^(?:(?:re|fw|fwd)\s*:\s*)+", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")

_WEIGHTS: dict[CorrelationIndicatorType, int] = {
    CorrelationIndicatorType.ATTACHMENT_SHA256: 6,
    CorrelationIndicatorType.URL: 4,
    CorrelationIndicatorType.SENDER_EMAIL: 4,
    CorrelationIndicatorType.REPLY_TO: 4,
    CorrelationIndicatorType.DOMAIN: 3,
    CorrelationIndicatorType.SENDER_DOMAIN: 2,
    CorrelationIndicatorType.REPLY_TO_DOMAIN: 2,
    CorrelationIndicatorType.IP_ADDRESS: 2,
    CorrelationIndicatorType.ASN: 1,
    CorrelationIndicatorType.NORMALIZED_SUBJECT: 1,
}

@dataclass(frozen=True)
class _Indicator:
    indicator_type: CorrelationIndicatorType
    value: str


def _normalized(value: str | None) -> str | None:
    if not value:
        return None
    compact = value.strip().casefold()
    return compact or None


def _domain(address: str | None) -> str | None:
    normalized = _normalized(address)
    if normalized is None or "@" not in normalized:
        return None
    local, domain = normalized.rsplit("@", 1)
    return domain if local and domain else None


def _normalized_subject(subject: str | None) -> str | None:
    normalized = _normalized(subject)
    if normalized is None:
        return None
    normalized = _SUBJECT_PREFIX.sub("", normalized)
    normalized = _WHITESPACE.sub(" ", normalized).strip()
    return normalized or None


def _indicator_reason(indicator: _Indicator) -> str:
    labels = {
        CorrelationIndicatorType.SENDER_EMAIL: "sender email",
        CorrelationIndicatorType.SENDER_DOMAIN: "sender domain",
        CorrelationIndicatorType.REPLY_TO: "Reply-To address",
        CorrelationIndicatorType.REPLY_TO_DOMAIN: "Reply-To domain",
        CorrelationIndicatorType.IP_ADDRESS: "observed routing IP",
        CorrelationIndicatorType.DOMAIN: "domain IOC",
        CorrelationIndicatorType.URL: "URL IOC",
        CorrelationIndicatorType.ATTACHMENT_SHA256: "attachment SHA-256",
        CorrelationIndicatorType.ASN: "observed infrastructure ASN",
        CorrelationIndicatorType.NORMALIZED_SUBJECT: "normalized subject pattern",
    }
    return f"Shared {labels[indicator.indicator_type]}: {indicator.value}"


def _indicators(analysis: EmailAnalysis) -> set[_Indicator]:
    """Return normalized, deduplicated values from persisted forensic output."""

    parsed = analysis.parsed_email
    if parsed is None:
        return set()

    values: set[_Indicator] = set()

    def add(indicator_type: CorrelationIndicatorType, value: str | None) -> None:
        normalized = _normalized(value)
        if normalized is not None:
            values.add(_Indicator(indicator_type, normalized))

    if parsed.sender:
        add(CorrelationIndicatorType.SENDER_EMAIL, parsed.sender.address)
        add(CorrelationIndicatorType.SENDER_DOMAIN, _domain(parsed.sender.address))
    for mailbox in parsed.reply_to:
        add(CorrelationIndicatorType.REPLY_TO, mailbox.address)
        add(CorrelationIndicatorType.REPLY_TO_DOMAIN, _domain(mailbox.address))

    add(CorrelationIndicatorType.NORMALIZED_SUBJECT, _normalized_subject(parsed.subject))
    for ip_address in parsed.originating_public_ips:
        add(CorrelationIndicatorType.IP_ADDRESS, ip_address)
    for ioc in parsed.iocs:
        correlation_type = {
            IOCType.IP_ADDRESS: CorrelationIndicatorType.IP_ADDRESS,
            IOCType.DOMAIN: CorrelationIndicatorType.DOMAIN,
            IOCType.URL: CorrelationIndicatorType.URL,
            IOCType.ATTACHMENT_SHA256: CorrelationIndicatorType.ATTACHMENT_SHA256,
        }.get(ioc.type)
        if correlation_type is not None:
            add(correlation_type, ioc.normalized_value)
    for attachment in parsed.attachments:
        add(CorrelationIndicatorType.ATTACHMENT_SHA256, attachment.sha256)
    for location in analysis.geolocations:
        add(CorrelationIndicatorType.ASN, location.asn or location.network)
    return values


def _strength(shared: set[_Indicator]) -> CorrelationStrength:
    types = {item.indicator_type for item in shared}
    derived_domains = {
        domain
        for item in shared
        if item.indicator_type
        in {CorrelationIndicatorType.SENDER_EMAIL, CorrelationIndicatorType.REPLY_TO}
        if (domain := _domain(item.value)) is not None
    }
    grouped_weights: dict[str, int] = {}
    for item in shared:
        if item.indicator_type in {
            CorrelationIndicatorType.SENDER_EMAIL,
            CorrelationIndicatorType.SENDER_DOMAIN,
        }:
            group = "sender"
        elif item.indicator_type in {
            CorrelationIndicatorType.REPLY_TO,
            CorrelationIndicatorType.REPLY_TO_DOMAIN,
        }:
            group = "reply-to"
        elif (
            item.indicator_type is CorrelationIndicatorType.DOMAIN
            and item.value in derived_domains
        ):
            # A domain extracted from an already shared address is useful to
            # display, but not independent corroboration.
            continue
        else:
            group = f"{item.indicator_type.value}:{item.value}"
        grouped_weights[group] = max(
            grouped_weights.get(group, 0), _WEIGHTS[item.indicator_type]
        )
    score = sum(grouped_weights.values())
    direct = {
        group
        for group in grouped_weights
        if group in {"sender", "reply-to"}
        or group.startswith(f"{CorrelationIndicatorType.URL.value}:")
    }
    if CorrelationIndicatorType.ATTACHMENT_SHA256 in types:
        return CorrelationStrength.HIGH
    if len(direct) >= 2 or (score >= 8 and len(grouped_weights) >= 2):
        return CorrelationStrength.HIGH
    if score >= 4 or len(types) >= 2:
        return CorrelationStrength.MEDIUM
    return CorrelationStrength.LOW


def _relationship_reasons(shared: set[_Indicator]) -> tuple[str, ...]:
    values = tuple(_indicator_reason(item) for item in sorted(shared, key=lambda item: (item.indicator_type.value, item.value)))
    types = {item.indicator_type for item in shared}
    if types <= {CorrelationIndicatorType.IP_ADDRESS, CorrelationIndicatorType.ASN}:
        return values + (
            "Shared routing infrastructure is weak corroboration and does not establish a shared sender or campaign.",
        )
    if types == {CorrelationIndicatorType.NORMALIZED_SUBJECT}:
        return values + (
            "A shared normalized subject is weak corroboration and should be reviewed with other evidence.",
        )
    return values


def correlate_case(
    target: EmailAnalysis,
    candidates: Iterable[EmailAnalysis],
    *,
    limit: int = 25,
    offset: int = 0,
) -> RelatedCasesResponse:
    """Find explainable potential relationships without claiming attribution."""

    target_indicators = _indicators(target)
    related: list[RelatedCase] = []
    for candidate in candidates:
        if candidate.case_id == target.case_id:
            continue
        shared = target_indicators & _indicators(candidate)
        if not shared:
            continue
        parsed = candidate.parsed_email
        ordered = tuple(
            SharedIndicator(
                indicator_type=item.indicator_type,
                value=item.value,
                reason=_indicator_reason(item),
            )
            for item in sorted(shared, key=lambda item: (item.indicator_type.value, item.value))
        )
        related.append(
            RelatedCase(
                case_id=candidate.case_id,
                subject=parsed.subject if parsed else None,
                risk_score=candidate.risk.score if candidate.risk else None,
                risk_severity=candidate.risk.severity if candidate.risk else None,
                shared_indicators=ordered,
                shared_indicator_count=len(ordered),
                correlation_strength=_strength(shared),
                relationship_reasons=_relationship_reasons(shared),
            )
        )

    rank = {
        CorrelationStrength.HIGH: 0,
        CorrelationStrength.MEDIUM: 1,
        CorrelationStrength.LOW: 2,
    }
    related.sort(
        key=lambda item: (
            rank[item.correlation_strength],
            -item.shared_indicator_count,
            str(item.case_id),
        )
    )
    return RelatedCasesResponse(
        case_id=target.case_id,
        items=tuple(related[offset : offset + limit]),
        total=len(related),
        limit=limit,
        offset=offset,
    )
