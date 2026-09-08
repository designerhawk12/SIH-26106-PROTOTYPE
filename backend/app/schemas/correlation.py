"""Read-only, deterministic cross-case correlation contracts."""

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from .email import ContractModel
from .enums import RiskLevel


class CorrelationIndicatorType(StrEnum):
    """Persisted forensic values eligible for explainable comparison."""

    SENDER_EMAIL = "SENDER_EMAIL"
    SENDER_DOMAIN = "SENDER_DOMAIN"
    REPLY_TO = "REPLY_TO"
    REPLY_TO_DOMAIN = "REPLY_TO_DOMAIN"
    IP_ADDRESS = "IP_ADDRESS"
    DOMAIN = "DOMAIN"
    URL = "URL"
    ATTACHMENT_SHA256 = "ATTACHMENT_SHA256"
    ASN = "ASN"
    NORMALIZED_SUBJECT = "NORMALIZED_SUBJECT"


class CorrelationStrength(StrEnum):
    """A deterministic screening aid, not attribution or campaign confirmation."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SharedIndicator(ContractModel):
    indicator_type: CorrelationIndicatorType
    value: str
    reason: str


class RelatedCase(ContractModel):
    case_id: UUID
    subject: str | None = None
    risk_score: int | None = Field(default=None, ge=0, le=100)
    risk_severity: RiskLevel | None = None
    shared_indicators: tuple[SharedIndicator, ...] = ()
    shared_indicator_count: int = Field(ge=1)
    correlation_strength: CorrelationStrength
    relationship_reasons: tuple[str, ...] = ()


class RelatedCasesResponse(ContractModel):
    case_id: UUID
    items: tuple[RelatedCase, ...] = ()
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    disclaimer: str = (
        "Potential relationships are deterministic comparisons of persisted "
        "forensic evidence. They do not establish a shared attacker, threat "
        "actor, or confirmed campaign."
    )
