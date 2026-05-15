"""Shared test fixtures — in-memory SQLite, isolated DB per test."""

from __future__ import annotations

import base64
import os
from collections.abc import Generator

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session", autouse=True)
def _set_env() -> None:
    """Set test env vars BEFORE bất kỳ import phongthuy_bds nào load Settings."""
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault(
        "API_SECRET_KEY",
        "test-secret-key-with-enough-bytes-1234567890",
    )
    # In-memory SQLite cho test nhanh. Lưu ý: enum + JSON khác Postgres; cẩn thận.
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault(
        "DLCN_ENCRYPTION_KEY",
        base64.urlsafe_b64encode(b"\0" * 32).decode(),
    )
    os.environ.setdefault("STORAGE_BACKEND", "local")
    os.environ.setdefault("STORAGE_LOCAL_PATH", "./.test_storage")
    os.environ.setdefault("OCR_BACKEND", "mock")


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Fresh in-memory SQLite per test."""
    from phongthuy_bds.db.base import Base
    from phongthuy_bds.db import models  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient với DB override."""
    from phongthuy_bds.db.session import get_db
    from phongthuy_bds.main import create_app

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def fernet_key() -> str:
    return base64.urlsafe_b64encode(b"\0" * 32).decode()
