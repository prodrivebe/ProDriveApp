"""SQLAlchemy engine and session management."""

from collections.abc import Generator
from typing import Final

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import Settings

_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None

DEFAULT_POOL_SIZE: Final[int] = 5
DEFAULT_MAX_OVERFLOW: Final[int] = 10
DEFAULT_POOL_TIMEOUT_SECONDS: Final[int] = 30
DEFAULT_POOL_RECYCLE_SECONDS: Final[int] = 1800


def init_engine(settings: Settings) -> Engine:
    """Create the SQLAlchemy engine and session factory."""
    global _engine, SessionLocal

    _engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=DEFAULT_POOL_SIZE,
        max_overflow=DEFAULT_MAX_OVERFLOW,
        pool_timeout=DEFAULT_POOL_TIMEOUT_SECONDS,
        pool_recycle=DEFAULT_POOL_RECYCLE_SECONDS,
    )
    SessionLocal = sessionmaker(
        bind=_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    return _engine


def get_engine() -> Engine:
    """Return the initialized SQLAlchemy engine."""
    if _engine is None:
        msg = "Database engine has not been initialized."
        raise RuntimeError(msg)
    return _engine


def dispose_engine() -> None:
    """Dispose of the SQLAlchemy engine."""
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        SessionLocal = None


def verify_database_connection() -> None:
    """Verify that the database connection is available."""
    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for request-scoped dependencies."""
    if SessionLocal is None:
        msg = "Database session factory has not been initialized."
        raise RuntimeError(msg)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
