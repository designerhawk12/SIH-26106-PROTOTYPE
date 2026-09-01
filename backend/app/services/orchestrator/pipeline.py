"""Infrastructure orchestration across injected feature-service ports."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from ...schemas import (
    AnalysisStatus,
    DetectionResult,
    EmailAnalysis,
    EnrichmentStatus,
    GeoLocationResult,
    GeoLocationStatus,
    ThreatIntelResult,
    TimelineEvent,
    TimelineEventType,
)
from .dependencies import (
    EmailForensicsService,
    GeoLocationService,
    RiskService,
    ThreatDetectionService,
    ThreatIntelService,
)


class EmailAnalysisError(Exception):
    """Raised when mandatory email parsing cannot produce normalized evidence."""


class AnalysisPipelineOrchestrator:
    """Coordinate services while containing optional-provider failures."""

    def __init__(
        self,
        *,
        email_forensics: EmailForensicsService,
        threat_detection: ThreatDetectionService,
        threat_intel: ThreatIntelService,
        geolocation: GeoLocationService,
        risk: RiskService,
    ) -> None:
        self._email_forensics = email_forensics
        self._threat_detection = threat_detection
        self._threat_intel = threat_intel
        self._geolocation = geolocation
        self._risk = risk

    async def analyze(
        self, raw_email: bytes, *, original_filename: str | None = None
    ) -> EmailAnalysis:
        created_at = datetime.now(timezone.utc)
        case_id = uuid4()
        warnings: list[str] = []

        try:
            parsed_email = self._email_forensics.parse(
                raw_email, original_filename=original_filename
            )
        except Exception as exc:
            raise EmailAnalysisError("Email parsing failed.") from exc

        try:
            detection = await self._threat_detection.detect(parsed_email)
        except Exception:  # noqa: BLE001 - optional service isolation boundary
            detection = DetectionResult(warnings=("Threat detection unavailable.",))
            warnings.append("Threat detection failed; analysis is partial.")

        try:
            threat_intel = await self._threat_intel.enrich(parsed_email.iocs)
        except Exception:  # noqa: BLE001 - provider isolation boundary
            threat_intel = ThreatIntelResult(
                status=EnrichmentStatus.UNAVAILABLE,
                requested_indicators=parsed_email.iocs,
                unknown_indicators=parsed_email.iocs,
                provider_errors=("Threat-intelligence provider unavailable.",),
            )
            warnings.append("Threat intelligence failed; reputation is UNKNOWN.")

        try:
            geolocations = await self._geolocation.locate_public_ips(
                parsed_email.originating_public_ips
            )
        except Exception:  # noqa: BLE001 - provider isolation boundary
            geolocations = tuple(
                GeoLocationResult(
                    ip_address=ip_address,
                    status=GeoLocationStatus.PROVIDER_ERROR,
                )
                for ip_address in parsed_email.originating_public_ips
            )
            warnings.append("Infrastructure geolocation failed; analysis is partial.")

        try:
            risk = self._risk.score(
                parsed_email=parsed_email,
                detection=detection,
                threat_intel=threat_intel,
                geolocations=geolocations,
            )
        except Exception:  # noqa: BLE001 - optional service isolation boundary
            risk = None
            warnings.append("Risk scoring failed; analysis is partial.")

        completed_at = datetime.now(timezone.utc)
        status = AnalysisStatus.PARTIAL if warnings else AnalysisStatus.COMPLETED
        timeline = (
            TimelineEvent(
                sequence=0,
                event_type=TimelineEventType.ANALYSIS_STARTED,
                timestamp=created_at,
                title="Analysis started",
                source="orchestrator",
            ),
            TimelineEvent(
                sequence=1,
                event_type=TimelineEventType.ANALYSIS_COMPLETED,
                timestamp=completed_at,
                title=(
                    "Analysis completed with partial results"
                    if warnings
                    else "Analysis completed"
                ),
                source="orchestrator",
            ),
        )
        return EmailAnalysis(
            case_id=case_id,
            status=status,
            original_filename=original_filename,
            created_at=created_at,
            completed_at=completed_at,
            parsed_email=parsed_email,
            detection=detection,
            threat_intel=threat_intel,
            geolocations=geolocations,
            risk=risk,
            timeline=timeline,
            warnings=tuple(warnings),
        )
