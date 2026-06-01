"""Tests for admin log routes — focuses on the conversation stats endpoint.

Regression: the stats endpoint previously filtered on ``ToolCall.created_at``,
a column that does not exist on the model (ToolCall only has ``started_at``),
which raised an AttributeError and surfaced as a 500 to the admin UI.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user, get_db_session
from app.core.config import settings
from app.main import app


class MockAdmin:
    """Mock admin user for testing role-protected endpoints."""

    def __init__(self) -> None:
        self.id = str(uuid4())
        self.email = "admin@example.com"
        self.full_name = "Admin"
        self.is_active = True
        self.role = "admin"
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def has_role(self, role) -> bool:
        if hasattr(role, "value"):
            return self.role == role.value
        return self.role == role


@pytest.fixture
def stats_db() -> MagicMock:
    """Mock DB session returning well-formed scalar/row results for stats queries."""
    result = MagicMock()
    result.scalar_one.return_value = 0
    result.all.return_value = []
    db = MagicMock()
    db.execute.return_value = result
    return db


@pytest.fixture
async def admin_client(stats_db: MagicMock) -> AsyncClient:
    """Client authenticated as admin with a mocked DB session."""
    admin = MockAdmin()
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[get_db_session] = lambda: stats_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_conversation_stats_returns_200(admin_client: AsyncClient):
    """The stats endpoint must not 500 — ToolCall is filtered by started_at."""
    response = await admin_client.get(
        f"{settings.API_V1_STR}/admin/logs/stats/conversations?days=30"
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_conversation_stats_response_contract(admin_client: AsyncClient):
    """Response keys must match the frontend ConversationStats contract."""
    response = await admin_client.get(
        f"{settings.API_V1_STR}/admin/logs/stats/conversations?days=30"
    )
    data = response.json()
    assert data["period_days"] == 30
    assert "total_messages" in data
    assert "user_messages" in data
    assert "rag_calls" in data
    assert "avg_rag_duration_ms" in data
    assert "tool_breakdown" in data
