"""Contracts for optional, non-authoritative AI investigation assistance."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator

from .email import ContractModel


class AIInvestigationAction(StrEnum):
    SUMMARY = "SUMMARY"
    SUSPICIOUS = "SUSPICIOUS"
    RECOMMENDED_ACTIONS = "RECOMMENDED_ACTIONS"
    AUTHENTICATION = "AUTHENTICATION"
    IOCS = "IOCS"
    ASK = "ASK"


class AIInvestigatorStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class AIInvestigationRequest(ContractModel):
    action: AIInvestigationAction = AIInvestigationAction.SUMMARY

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, value: object) -> object:
        if isinstance(value, str):
            value = AIInvestigationAction(value.strip().upper())
        if value is AIInvestigationAction.ASK:
            raise ValueError("ASK is only valid for the dedicated question endpoint.")
        return value


class AIAskRequest(ContractModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question", mode="before")
    @classmethod
    def normalize_question(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AIInvestigatorResponse(ContractModel):
    status: AIInvestigatorStatus
    action: AIInvestigationAction
    model: str | None = None
    generated_at: datetime
    ai_generated: Literal[True] = True
    simulated: bool = False
    summary: str
    key_findings: tuple[str, ...] = ()
    risk_explanation: str
    recommended_actions: tuple[str, ...] = ()
    ioc_summary: str
    limitations: tuple[str, ...] = ()
    answer: str | None = None
    disclaimer: str = (
        "AI-generated interpretation is assistive only. Persisted forensic facts and "
        "the deterministic risk engine remain authoritative."
    )
