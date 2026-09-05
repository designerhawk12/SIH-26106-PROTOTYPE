"""FastAPI application factory and default ASGI application."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from .app.api import (
    auth_router,
    cases_router,
    health_router,
    infrastructure_router,
    threat_intelligence_router,
)
from .app.core import Settings, get_settings, install_exception_handlers
from .app.core.middleware import RequestIdMiddleware
from .app.db import create_database_engine, create_session_factory, initialize_database
from .app.services.auth.interfaces import IdentityVerifier
from .app.services.orchestrator.interfaces import AnalysisOrchestrator
from .app.services.reporting.interfaces import ReportingService


def create_app(
    *,
    settings: Settings | None = None,
    analysis_orchestrator: AnalysisOrchestrator | None = None,
    reporting_service: ReportingService | None = None,
    identity_verifier: IdentityVerifier | None = None,
    database_engine: Engine | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> FastAPI:
    runtime_settings = settings or get_settings()
    engine = database_engine or create_database_engine(runtime_settings.database_url)
    factory = session_factory or create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await run_in_threadpool(initialize_database, engine)
        yield
        await run_in_threadpool(engine.dispose)

    application = FastAPI(
        title="Email Threat Detection and Forensic Intelligence API",
        version=runtime_settings.app_version,
        lifespan=lifespan,
    )
    application.state.settings = runtime_settings
    application.state.analysis_orchestrator = analysis_orchestrator
    application.state.reporting_service = reporting_service
    application.state.identity_verifier = identity_verifier
    application.state.database_engine = engine
    application.state.session_factory = factory

    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(runtime_settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )
    install_exception_handlers(application)
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(cases_router)
    application.include_router(threat_intelligence_router)
    application.include_router(infrastructure_router)
    return application


app = create_app()

