"""Integration tests for the Phase C notification REST endpoints.

  GET  /notifications                  — inbox + unread badge count
  POST /notifications/{id}/read        — mark one read
  POST /notifications/read-all         — mark all read

Same wiring approach as test_routes_phase_b.py: override the DB session,
current user, and the notification service factory so routes hit our in-memory
SQLite session and a fake authenticated user.
"""

from collections.abc import AsyncGenerator
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import (
    get_commercial_notification_service,
    get_current_user,
    get_db_session,
)
from app.main import app
from app.repositories import commercial_notification_repo as notif_repo
from app.services.commercial_notification_service import CommercialNotificationService


@pytest.fixture
def fake_user(db, user_id):
    return SimpleNamespace(id=user_id, email="test@local", is_active=True)


@pytest.fixture
async def http(db, fake_user) -> AsyncGenerator[AsyncClient, None]:
    def _db():
        yield db

    app.dependency_overrides[get_db_session] = _db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_commercial_notification_service] = lambda: (
        CommercialNotificationService(db)
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


def _make_other_user(db, suffix: str) -> str:
    from app.db.models.user import User

    other = f"00000000-0000-4000-8000-0000000000{suffix}"
    db.add(User(id=other, email=f"{suffix}@test.local", hashed_password="x" * 60))
    db.flush()
    return other


class TestNotificationEndpoints:
    @pytest.mark.anyio
    async def test_list_returns_unread_badge(self, http, db, user_id):
        notif_repo.create(db, user_id=user_id, type="renewal_due", title="a", read=False)
        notif_repo.create(db, user_id=user_id, type="deal_debrief", title="b", read=True)
        db.commit()

        resp = await http.get("/api/v1/commercial/notifications")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 2
        assert body["unread"] == 1

    @pytest.mark.anyio
    async def test_list_unread_only(self, http, db, user_id):
        notif_repo.create(db, user_id=user_id, type="renewal_due", read=False)
        notif_repo.create(db, user_id=user_id, type="deal_debrief", read=True)
        db.commit()

        resp = await http.get("/api/v1/commercial/notifications?unread_only=true")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["unread"] == 1

    @pytest.mark.anyio
    async def test_mark_one_read(self, http, db, user_id):
        n = notif_repo.create(db, user_id=user_id, type="renewal_due", read=False)
        db.commit()

        resp = await http.post(f"/api/v1/commercial/notifications/{n.id}/read")
        assert resp.status_code == 200, resp.text
        assert resp.json()["read"] is True

    @pytest.mark.anyio
    async def test_mark_read_404_when_missing(self, http):
        resp = await http.post(
            "/api/v1/commercial/notifications/00000000-0000-0000-0000-000000000000/read"
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_mark_read_blocks_cross_user(self, http, db):
        other = _make_other_user(db, "50")
        n = notif_repo.create(db, user_id=other, type="renewal_due", read=False)
        db.commit()

        resp = await http.post(f"/api/v1/commercial/notifications/{n.id}/read")
        assert resp.status_code == 403

    @pytest.mark.anyio
    async def test_mark_all_read(self, http, db, user_id):
        notif_repo.create(db, user_id=user_id, type="renewal_due", read=False)
        notif_repo.create(db, user_id=user_id, type="deal_debrief", read=False)
        db.commit()

        resp = await http.post("/api/v1/commercial/notifications/read-all")
        assert resp.status_code == 200, resp.text
        assert resp.json()["updated"] == 2

        listing = await http.get("/api/v1/commercial/notifications")
        assert listing.json()["unread"] == 0
