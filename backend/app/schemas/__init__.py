"""Authoritative public exports for shared contracts."""

from .analysis import EmailAnalysis, TimelineEvent
from .auth import (
    Permission,
    UpdateProfileRequest,
    UpdateRoleRequest,
    UserListResponse,
    UserProfile,
    UserRole,
)
from .api import (
    AnalyzeCaseResponse,
    CaseListResponse,
    CaseSummary,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
)
from .detection import DetectionFinding, DetectionResult
from .email import (
    AttachmentEvidence,
    AuthenticationResults,
    ContractModel,
    ExtractedIOC,
    MailboxAddress,
    MimePart,
    ParsedEmail,
    ReceivedHop,
)
from .enums import (
    AnalysisStatus,
    AuthenticationVerdict,
    DetectionCategory,
    EnrichmentStatus,
    GeoLocationStatus,
    IOCSource,
    IOCType,
    ReputationVerdict,
    RiskLevel,
    Severity,
    TimelineEventType,
)
from .risk import RiskReason, RiskResult
from .threat_intel import GeoLocationResult, ThreatFinding, ThreatIntelResult

__all__ = [
    "AnalysisStatus",
    "AnalyzeCaseResponse",
    "AttachmentEvidence",
    "AuthenticationResults",
    "AuthenticationVerdict",
    "CaseListResponse",
    "CaseSummary",
    "ContractModel",
    "DetectionCategory",
    "DetectionFinding",
    "DetectionResult",
    "EmailAnalysis",
    "EnrichmentStatus",
    "ErrorDetail",
    "ErrorResponse",
    "ExtractedIOC",
    "GeoLocationResult",
    "GeoLocationStatus",
    "HealthResponse",
    "IOCSource",
    "IOCType",
    "MailboxAddress",
    "MimePart",
    "ParsedEmail",
    "Permission",
    "ReceivedHop",
    "ReputationVerdict",
    "RiskLevel",
    "RiskReason",
    "RiskResult",
    "Severity",
    "ThreatFinding",
    "ThreatIntelResult",
    "TimelineEvent",
    "TimelineEventType",
    "UpdateProfileRequest",
    "UpdateRoleRequest",
    "UserListResponse",
    "UserProfile",
    "UserRole",
]
