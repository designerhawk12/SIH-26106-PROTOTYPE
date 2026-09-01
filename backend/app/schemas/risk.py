"""Contracts for deterministic, explainable risk scoring."""

from pydantic import Field

from .email import ContractModel
from .enums import RiskLevel


class RiskReason(ContractModel):
    code: str
    description: str
    points: int
    evidence_refs: tuple[str, ...] = ()


class RiskResult(ContractModel):
    score: int = Field(ge=0, le=100)
    severity: RiskLevel
    reasons: tuple[RiskReason, ...] = ()
    formula_version: str
    unknown_inputs: tuple[str, ...] = Field(
        default=(), description="Unavailable signals that were not treated as safe."
    )
