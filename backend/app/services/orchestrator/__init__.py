"""Analysis-orchestration contracts and infrastructure pipeline."""

from .factory import build_default_analysis_orchestrator
from .interfaces import AnalysisOrchestrator
from .pipeline import AnalysisPipelineOrchestrator, EmailAnalysisError

__all__ = [
    "AnalysisOrchestrator",
    "AnalysisPipelineOrchestrator",
    "EmailAnalysisError",
    "build_default_analysis_orchestrator",
]
