"""Build safe, read-only system status metadata from runtime configuration."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from ..core import Settings
from ..schemas import (
    SystemComponentStatus,
    SystemStatusResponse,
    SystemStatusState,
)


def _is_configured(variable: str) -> bool:
    """Check only whether an environment variable is populated, never return it."""

    return bool(os.getenv(variable, "").strip())


def _configured_component(label: str, configured: bool, detail: str) -> SystemComponentStatus:
    return SystemComponentStatus(
        label=label,
        state=(SystemStatusState.CONFIGURED if configured else SystemStatusState.NOT_CONFIGURED),
        detail=detail if configured else "Not configured for this deployment.",
    )


def _database_component(settings: Settings) -> SystemComponentStatus:
    scheme = urlparse(settings.database_url).scheme.casefold()
    if scheme.startswith("postgres"):
        label = (
            "Supabase PostgreSQL"
            if "supabase" in settings.database_url.casefold() or settings.supabase_url
            else "PostgreSQL"
        )
        return SystemComponentStatus(
            label=label,
            state=SystemStatusState.OPERATIONAL,
            detail="Hosted PostgreSQL persistence is selected.",
        )
    return SystemComponentStatus(
        label="SQLite Development Fallback",
        state=SystemStatusState.OPERATIONAL,
        detail="Local SQLite persistence is selected.",
    )


def build_system_status(settings: Settings) -> SystemStatusResponse:
    """Return deployment status without making provider calls or exposing secrets."""

    demo_state = SystemStatusState.ENABLED if settings.demo_mode else SystemStatusState.DISABLED
    geolocation_state = (
        SystemStatusState.SIMULATED if settings.demo_mode else SystemStatusState.AVAILABLE
    )

    return SystemStatusResponse(
        backend=SystemComponentStatus(
            label="FastAPI Backend",
            state=SystemStatusState.OPERATIONAL,
            detail="Application service is running.",
        ),
        database=_database_component(settings),
        authentication=_configured_component(
            "Supabase Auth",
            bool(settings.supabase_url and settings.supabase_publishable_key),
            "Supabase Auth verification is configured.",
        ),
        demo_mode=SystemComponentStatus(
            label="Demo Mode",
            state=demo_state,
            detail=(
                "Synthetic enrichment may be used and is labelled as simulated."
                if settings.demo_mode
                else "Synthetic enrichment is disabled."
            ),
        ),
        threat_intelligence=(
            _configured_component(
                "AbuseIPDB",
                _is_configured("ABUSEIPDB_API_KEY"),
                "Threat-intelligence provider is configured.",
            ),
            _configured_component(
                "VirusTotal",
                _is_configured("VIRUSTOTAL_API_KEY"),
                "Threat-intelligence provider is configured.",
            ),
        ),
        geolocation=SystemComponentStatus(
            label="Observed Infrastructure Geolocation",
            state=geolocation_state,
            detail=(
                "Demo geolocation is enabled; results are simulated."
                if settings.demo_mode
                else "Observed mail-routing infrastructure geolocation is available."
            ),
        ),
        ai_investigator=_configured_component(
            "AI Investigator (Groq)",
            settings.groq_api_key is not None,
            "The backend-only AI Investigator integration is configured.",
        ),
    )
