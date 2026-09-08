"""Optional Groq-powered investigation assistant."""

from .factory import build_ai_investigator_service
from .interfaces import AIInvestigatorService

__all__ = ["AIInvestigatorService", "build_ai_investigator_service"]
