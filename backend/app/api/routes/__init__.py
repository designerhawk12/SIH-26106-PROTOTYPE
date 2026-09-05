"""Versioned API route modules."""

from .auth import router as auth_router
from .cases import router as cases_router
from .health import router as health_router
from .infrastructure import router as infrastructure_router
from .threat_intelligence import router as threat_intelligence_router

__all__ = [
    "auth_router",
    "cases_router",
    "health_router",
    "infrastructure_router",
    "threat_intelligence_router",
]

