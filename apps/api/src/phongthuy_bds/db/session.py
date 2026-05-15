"""SQLAlchemy session + engine."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from phongthuy_bds.core.config import get_settings


def _make_engine():
    settings = get_settings()
    kwargs: dict = {"pool_pre_ping": True}
    # SQLite (test) dùng SingletonThreadPool, không hỗ trợ pool_size/max_overflow.
    if not settings.database_url.startswith("sqlite"):
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
    return create_engine(settings.database_url, **kwargs)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yield một session, đảm bảo close."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
