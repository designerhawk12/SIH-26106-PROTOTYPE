"""Sanitized, read-only runtime configuration contracts."""

from enum import StrEnum

from .email import ContractModel


class SystemStatusState(StrEnum):
    """Safe operational states; they never contain configuration values."""

    OPERATIONAL = "OPERATIONAL"
    CONFIGURED = "CONFIGURED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    AVAILABLE = "AVAILABLE"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    SIMULATED = "SIMULATED"


class SystemComponentStatus(ContractModel):
    """A human-readable component state without credentials or endpoints."""

    label: str
    state: SystemStatusState
    detail: str


class SystemStatusResponse(ContractModel):
    """Administrator-visible metadata for the local Sentinel MX deployment."""

    backend: SystemComponentStatus
    database: SystemComponentStatus
    authentication: SystemComponentStatus
    demo_mode: SystemComponentStatus
    threat_intelligence: tuple[SystemComponentStatus, ...]
    geolocation: SystemComponentStatus
    ai_investigator: SystemComponentStatus
