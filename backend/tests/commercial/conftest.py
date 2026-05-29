"""Test fixtures for commercial-legal repositories.

Uses an in-memory SQLite database with the project's SQLAlchemy
`Base.metadata.create_all()` to materialize the schema. This lets us
exercise real constraints (UNIQUE, NOT NULL, ON DELETE CASCADE) and
real JSON round-trips, which mock-based tests can't catch.

The DB is reset per test (function-scoped engine + session).
"""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Importing the models package ensures all tables get registered onto
# Base.metadata before create_all runs.
from app.db import models  # noqa: F401
from app.db.base import Base


@pytest.fixture
def engine():
    """Fresh in-memory SQLite engine per test.

    `check_same_thread=False` is required because FastAPI's threadpool
    runs sync routes off the main thread, but the fixture creates the
    connection on the main thread.
    """
    # StaticPool keeps a single shared connection — required because
    # in-memory SQLite is per-connection (each new connection sees an
    # empty database). FastAPI's thread pool would otherwise grab a
    # different connection per request and miss our tables.
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Foreign keys are off by default on SQLite. Turn them on so the
    # ON DELETE CASCADE relationships actually fire in tests.
    @event.listens_for(eng, "connect")
    def _enable_fk(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    """A SQLAlchemy session bound to the per-test engine."""
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def user_id(db) -> str:
    """Create a real User row so FK-bearing rows can reference it."""
    import uuid

    from app.db.models.user import User

    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=f"{uid[:8]}@test.local",
        hashed_password="x" * 60,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return uid
