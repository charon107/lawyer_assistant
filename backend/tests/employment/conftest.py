"""Test fixtures for employment-legal — in-memory SQLite with real schema.

Mirrors tests/corporate/conftest.py: function-scoped in-memory engine, FK
enforcement on, real JSON round-trips.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import models  # noqa: F401  (register tables on Base.metadata)
from app.db.base import Base


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

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
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def user_id(db) -> str:
    import uuid

    from app.db.models.user import User

    uid = str(uuid.uuid4())
    user = User(id=uid, email=f"{uid[:8]}@test.local", hashed_password="x" * 60, is_active=True)
    db.add(user)
    db.flush()
    return uid
