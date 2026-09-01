"""Contracts for reputation enrichment and infrastructure geolocation."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from .email import ContractModel, ExtractedIOC
from .enums import (
    EnrichmentStatus,
    GeoLocationStatus,
    IOCType,
    ReputationVerdict,
)


class ThreatFinding(ContractModel):
    indicator_type: IOCType
    indicator: str
    provider: str
    verdict: ReputationVerdict = ReputationVerdict.UNKNOWN
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    categories: tuple[str, ...] = ()
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    reference: str | None = Field(
        default=None, description="Provider reference; consumers must not auto-visit it."
    )
    details: str | None = None


class ThreatIntelResult(ContractModel):
    status: EnrichmentStatus = EnrichmentStatus.UNKNOWN
    requested_indicators: tuple[ExtractedIOC, ...] = ()
    findings: tuple[ThreatFinding, ...] = ()
    unknown_indicators: tuple[ExtractedIOC, ...] = ()
    provider_errors: tuple[str, ...] = Field(
        default=(), description="Sanitized errors; must never contain provider secrets."
    )


class GeoLocationResult(ContractModel):
    ip_address: str
    status: GeoLocationStatus = GeoLocationStatus.UNKNOWN
    country: str | None = None
    country_code: str | None = None
    city: str | None = None
    region: str | None = None
    isp: str | None = None
    asn: str | None = None
    organization: str | None = None
    network: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    provider: str | None = None
    observed_infrastructure_only: Literal[True] = Field(
        default=True,
        description="Always true: this is observed routing infrastructure, not attacker location.",
    )
