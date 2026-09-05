"""Read-only contracts for the persisted threat-intelligence workspace."""

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import Field

from .email import ContractModel
from .enums import IOCType


class IntelligenceStatus(StrEnum):
    MALICIOUS = "MALICIOUS"
    SUSPICIOUS = "SUSPICIOUS"
    BENIGN = "BENIGN"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"


class ProviderWorkspaceStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ThreatCaseReference(ContractModel):
    case_id: UUID
    subject: str | None = None
    original_filename: str | None = None


class ThreatIOCRecord(ContractModel):
    ioc_type: IOCType
    value: str
    status: IntelligenceStatus
    providers: tuple[str, ...] = ()
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    categories: tuple[str, ...] = ()
    details: tuple[str, ...] = ()
    filename: str | None = None
    associated_cases: tuple[ThreatCaseReference, ...] = ()
    demo: bool = False


class ThreatSummary(ContractModel):
    total_observed_iocs: int = Field(ge=0)
    suspicious_or_malicious: int = Field(ge=0)
    benign: int = Field(ge=0)
    unknown: int = Field(ge=0)
    unavailable: int = Field(ge=0)


class ProviderStatusRecord(ContractModel):
    name: str
    category: Literal["THREAT_INTELLIGENCE", "GEOLOCATION"]
    status: ProviderWorkspaceStatus
    demo: bool = False
    messages: tuple[str, ...] = ()


class ThreatIntelligenceWorkspace(ContractModel):
    summary: ThreatSummary
    indicators: tuple[ThreatIOCRecord, ...] = ()
    providers: tuple[ProviderStatusRecord, ...] = ()
    cases_scanned: int = Field(ge=0)

