"""Composition root for the production analysis pipeline."""

from ..detection import DeterministicDetectionService
from ..email_forensics import EmailForensicsParser
from ..geolocation import IpWhoIsProvider, ObservedInfrastructureGeoService
from ..risk import DeterministicRiskEngine
from ..threat_intel import (
    AbuseIPDBProvider,
    ThreatIntelEnrichmentService,
    VirusTotalProvider,
)
from .pipeline import AnalysisPipelineOrchestrator


def build_default_analysis_orchestrator() -> AnalysisPipelineOrchestrator:
    """Build the application pipeline from existing public service adapters.

    Provider adapters read credentials only from their own environment-backed
    constructors. Missing credentials produce controlled unavailable results.
    """

    return AnalysisPipelineOrchestrator(
        email_forensics=EmailForensicsParser(),
        threat_detection=DeterministicDetectionService(),
        threat_intel=ThreatIntelEnrichmentService(
            providers=(
                AbuseIPDBProvider.from_environment(),
                VirusTotalProvider.from_environment(),
            )
        ),
        geolocation=ObservedInfrastructureGeoService(provider=IpWhoIsProvider()),
        risk=DeterministicRiskEngine(),
    )
