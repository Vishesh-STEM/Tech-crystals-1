"""Engine / session factory with a PostgreSQL -> SQLite development fallback."""
from __future__ import annotations

import logging
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

ACTIVE_DATABASE_URL = settings.DATABASE_URL
USING_FALLBACK = False


def _make_engine(url: str) -> Engine:
    kwargs = {"echo": settings.SQL_ECHO, "pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def _build_engine() -> Engine:
    """Connect to the configured database, or fall back to SQLite for development.

    Everything that can go wrong at start-up is handled: an unreachable server,
    bad credentials, a malformed URL, and a missing driver (for example
    PostgreSQL configured but ``psycopg2`` not installed), which raises
    ImportError from ``create_engine`` rather than a SQLAlchemy error.
    """
    global ACTIVE_DATABASE_URL, USING_FALLBACK
    try:
        candidate = _make_engine(settings.DATABASE_URL)
        with candidate.connect():
            pass
        return candidate
    except Exception as exc:  # pragma: no cover - depends on environment
        if not settings.ALLOW_SQLITE_FALLBACK or settings.DATABASE_URL.startswith("sqlite"):
            raise
        hint = ""
        if isinstance(exc, (ImportError, ModuleNotFoundError)):
            hint = " (database driver not installed - `pip install psycopg2-binary`)"
        elif isinstance(exc, ArgumentError):
            hint = " (DATABASE_URL could not be parsed)"
        logger.warning(
            "Database %s unavailable: %s%s. Falling back to the SQLite development "
            "database %s. Set ALLOW_SQLITE_FALLBACK=false to fail instead.",
            settings.DATABASE_URL.split("@")[-1],
            exc.__class__.__name__,
            hint,
            settings.SQLITE_FALLBACK_URL,
        )
        ACTIVE_DATABASE_URL = settings.SQLITE_FALLBACK_URL
        USING_FALLBACK = True
        return _make_engine(settings.SQLITE_FALLBACK_URL)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # pragma: no cover
    """Enforce foreign keys on SQLite so constraints behave like PostgreSQL."""
    if ACTIVE_DATABASE_URL.startswith("sqlite"):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception:
            pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
