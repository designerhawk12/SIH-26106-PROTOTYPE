"""Aggregate case and forensic timeline contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from .detection import DetectionResult
from .email import ContractModel, ParsedEmail
from .enums import AnalysisStatus, TimelineEventType
from .risk import RiskResult
from .threat_intel import GeoLocationResult, ThreatIntelResult


class TimelineEvent(ContractModel):
    sequence: int = Field(ge=0)
    event_type: TimelineEventType
    timestamp: datetime | None = None
    title: str
    description: str | None = None
    source: str
    evidence_refs: tuple[str, ...] = ()


class EmailAnalysis(ContractModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    case_id: UUID
    status: AnalysisStatus
    original_filename: str | None = Field(
        default=None,
        description="Untrusted display metadata only; never use as a storage path.",
    )
    created_at: datetime
    completed_at: datetime | None = None
    parsed_email: ParsedEmail | None = None
    detection: DetectionResult | None = None
    threat_intel: ThreatIntelResult | None = None
    geolocations: tuple[GeoLocationResult, ...] = ()
    risk: RiskResult | None = None
    timeline: tuple[TimelineEvent, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = Field(
        default=(), description="Sanitized errors; must not contain secrets."
    )
