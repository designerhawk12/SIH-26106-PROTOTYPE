"""Composition root for the production analysis pipeline."""

from ...core import Settings, get_settings
from ..detection import DeterministicDetectionService
from ..email_forensics import EmailForensicsParser
from ..geolocation import (
    DemoInfrastructureGeoProvider,
    IpWhoIsProvider,
    ObservedInfrastructureGeoService,
)
from ..risk import DeterministicRiskEngine
from ..threat_intel import (
    AbuseIPDBProvider,
    DemoThreatIntelProvider,
    ThreatIntelEnrichmentService,
    VirusTotalProvider,
)
from .pipeline import AnalysisPipelineOrchestrator

DEMO_MODE_WARNING = (
    "DEMO MODE: threat-intelligence and infrastructure geolocation results may be "
    "synthetic and are not verified live provider results. Email evidence, hashes, "
    "deterministic detection, and deterministic risk remain real."
)


def build_default_analysis_orchestrator(
    settings: Settings | None = None,
) -> AnalysisPipelineOrchestrator:
    """Build the application pipeline from existing public service adapters.

    Provider adapters read credentials only from their own environment-backed
    constructors. Missing credentials produce controlled unavailable results.
    """

    runtime_settings = settings or get_settings()
    if runtime_settings.demo_mode:
        threat_intel = ThreatIntelEnrichmentService(
            providers=(DemoThreatIntelProvider(),)
        )
        geolocation = ObservedInfrastructureGeoService(
            provider=DemoInfrastructureGeoProvider()
        )
        mode_warnings = (DEMO_MODE_WARNING,)
    else:
        threat_intel = ThreatIntelEnrichmentService(
            providers=(
                AbuseIPDBProvider.from_environment(),
                VirusTotalProvider.from_environment(),
            )
        )
        geolocation = ObservedInfrastructureGeoService(provider=IpWhoIsProvider())
        mode_warnings = ()

    return AnalysisPipelineOrchestrator(
        email_forensics=EmailForensicsParser(),
        threat_detection=DeterministicDetectionService(),
        threat_intel=threat_intel,
        geolocation=geolocation,
        risk=DeterministicRiskEngine(),
        mode_warnings=mode_warnings,
    )
