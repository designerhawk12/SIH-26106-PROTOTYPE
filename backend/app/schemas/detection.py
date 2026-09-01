"""Contracts for explainable AI/content threat findings."""

from pydantic import Field

from .email import ContractModel
from .enums import DetectionCategory, Severity


class DetectionFinding(ContractModel):
    finding_id: str
    category: DetectionCategory
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    title: str
    explanation: str
    evidence: tuple[str, ...] = Field(
        default=(), description="Short escaped excerpts or stable evidence references."
    )
    detector: str


class DetectionResult(ContractModel):
    findings: tuple[DetectionFinding, ...] = ()
    model_name: str | None = None
    model_version: str | None = None
    summary: str | None = None
    warnings: tuple[str, ...] = ()

