"""Database engine and session construction."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .base import Base


def create_database_engine(database_url: str) -> Engine:
    """Create an engine compatible with SQLite now and PostgreSQL later."""

    options: dict[str, object] = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            options["poolclass"] = StaticPool
    return create_engine(database_url, **options)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def initialize_database(engine: Engine) -> None:
    """Create the current MVP tables; migrations can replace this at deployment."""

    Base.metadata.create_all(bind=engine)

