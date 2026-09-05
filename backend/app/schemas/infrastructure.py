"""Read-only views over persisted infrastructure evidence; no new storage model."""

from datetime import datetime
from uuid import UUID

from .email import ContractModel
from .enums import AnalysisStatus, EnrichmentStatus, ReputationVerdict, RiskLevel
from .threat_intel import GeoLocationResult


class InfrastructureCase(ContractModel):
    case_id: UUID
    subject: str | None = None
    status: AnalysisStatus
    risk_severity: RiskLevel | None = None


class InfrastructureObservation(ContractModel):
    id: str
    ip_address: str
    case: InfrastructureCase
    observed_at: datetime
    location: GeoLocationResult | None = None
    verdict: ReputationVerdict = ReputationVerdict.UNKNOWN
    threat_intel_status: EnrichmentStatus = EnrichmentStatus.UNKNOWN
    threat_providers: tuple[str, ...] = ()
    demo: bool = False


class InfrastructureRouteSegment(ContractModel):
    case_id: UUID
    from_observation_id: str
    to_observation_id: str
    from_timestamp: datetime
    to_timestamp: datetime


class InfrastructureWorkspace(ContractModel):
    observations: tuple[InfrastructureObservation, ...] = ()
    route_segments: tuple[InfrastructureRouteSegment, ...] = ()
    cases_scanned: int = 0
    disclaimer: str = (
        "Observed infrastructure geolocation does not establish the physical "
        "location or identity of an attacker."
    )
