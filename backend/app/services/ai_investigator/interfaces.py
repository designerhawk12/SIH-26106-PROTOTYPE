"""Provider and service boundaries for assistive AI investigation."""

from typing import Any, Protocol

from ...schemas import AIInvestigationAction, AIInvestigatorResponse, EmailAnalysis


class AIProviderError(Exception):
    """A sanitized provider failure safe to normalize at the service boundary."""


class AIProviderAuthenticationError(AIProviderError):
    pass


class AIProviderQuotaError(AIProviderError):
    pass


class AIProviderTimeoutError(AIProviderError):
    pass


class AIProviderUnavailableError(AIProviderError):
    pass


class AIProviderMalformedResponseError(AIProviderError):
    pass


class AIProviderConfigurationError(AIProviderError):
    pass


class AIProviderModelUnavailableError(AIProviderError):
    pass


class AIProviderTruncatedResponseError(AIProviderMalformedResponseError):
    """A structured response could not be completed before the token limit."""

    pass


class GroqProvider(Protocol):
    model_name: str

    async def generate(
        self,
        *,
        system_instruction: str,
        prompt: str,
        response_schema: dict[str, Any],
    ) -> dict[str, Any]: ...


class AIInvestigatorService(Protocol):
    async def investigate(
        self, analysis: EmailAnalysis, action: AIInvestigationAction
    ) -> AIInvestigatorResponse: ...

    async def ask(
        self, analysis: EmailAnalysis, question: str
    ) -> AIInvestigatorResponse: ...
