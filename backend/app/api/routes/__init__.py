"""Versioned API route modules."""

from .ai_investigator import router as ai_investigator_router
from .auth import router as auth_router
from .cases import router as cases_router
from .extension import router as extension_router
from .health import router as health_router
from .infrastructure import router as infrastructure_router
from .system import router as system_router
from .threat_intelligence import router as threat_intelligence_router
from .workflow import cases_router as workflow_cases_router, watchlist_router

__all__ = [
    "ai_investigator_router",
    "auth_router",
    "cases_router",
    "extension_router",
    "health_router",
    "infrastructure_router",
    "system_router",
    "threat_intelligence_router",
    "watchlist_router",
    "workflow_cases_router",
]