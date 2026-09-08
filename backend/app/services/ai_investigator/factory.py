"""Construct the Groq-backed AI investigator from environment settings."""

from ...core import Settings
from .interfaces import AIInvestigatorService
from .provider import GroqHTTPProvider
from .service import (
    DemoAIInvestigatorService,
    LiveAIInvestigatorService,
    UnavailableAIInvestigatorService,
)


def build_ai_investigator_service(settings: Settings) -> AIInvestigatorService:
    if settings.groq_api_key is not None:
        return LiveAIInvestigatorService(
            GroqHTTPProvider(
                api_key=settings.groq_api_key.get_secret_value(),
                model_name=settings.groq_model,
                timeout_seconds=settings.groq_timeout_seconds,
            )
        )
    if settings.demo_mode:
        return DemoAIInvestigatorService()
    return UnavailableAIInvestigatorService(settings.groq_model)
