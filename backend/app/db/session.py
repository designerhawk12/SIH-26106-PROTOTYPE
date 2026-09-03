"""Database engine and session construction."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .base import Base


def normalize_database_url(database_url: str) -> str:
    """Select Psycopg 3 for standard PostgreSQL/Supabase connection URLs."""

    normalized = database_url.strip()
    if not normalized:
        raise ValueError("DATABASE_URL must not be empty.")
    if normalized.startswith("postgres://"):
        return normalized.replace("postgres://", "postgresql+psycopg://", 1)
    if normalized.startswith("postgresql://"):
        return normalized.replace("postgresql://", "postgresql+psycopg://", 1)
    return normalized


def create_database_engine(database_url: str) -> Engine:
    """Create a pooled engine for SQLite or PostgreSQL/Supabase."""

    database_url = normalize_database_url(database_url)
    options: dict[str, object] = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            options["poolclass"] = StaticPool
    return create_engine(database_url, **options)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def initialize_database(engine: Engine) -> None:
    """Create local SQLite tables; PostgreSQL schemas are Alembic-managed."""

    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(bind=engine)

