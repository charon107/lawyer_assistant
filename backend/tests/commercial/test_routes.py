"""Integration tests for the commercial-legal REST endpoints.

We wire dependency overrides so the routes actually hit our in-memory
SQLite session + a fake current user, and assert on HTTP-level
behavior (status codes, response shapes).

We do NOT exercise the WebSocket here. WS streaming is tested
through manual E2E in Week 4.
"""

from collections.abc import AsyncGenerator
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import (
    get_cold_start_service,
    get_commercial_profile_service,
    get_contract_review_service,
    get_current_user,
    get_db_session,
)
from app.main import app
from app.services.cold_start_service import ColdStartService
from app.services.commercial_profile_service import CommercialProfileService
from app.services.contract_review_service import ContractReviewService


@pytest.fixture
def fake_user(db, user_id):
    """A lightweight stand-in for `User` the auth dependency returns.

    Using SimpleNamespace rather than MagicMock so attribute access
    returns real strings (MagicMock's default `.id` is itself a
    MagicMock that str()'s to `<MagicMock id=...>` which then makes
    the DB query break).
    """
    return SimpleNamespace(
        id=user_id,
        email="test@local",
        is_active=True,
    )


@pytest.fixture
async def http(db, fake_user) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX async client with all commercial deps wired to our test DB."""

    def _db():
        yield db

    app.dependency_overrides[get_db_session] = _db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_commercial_profile_service] = lambda: CommercialProfileService(db)
    app.dependency_overrides[get_contract_review_service] = lambda: ContractReviewService(db)
    app.dependency_overrides[get_cold_start_service] = lambda: ColdStartService(db)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /status
# ---------------------------------------------------------------------------


class TestModuleStatus:
    @pytest.mark.anyio
    async def test_status_when_no_profile(self, http):
        resp = await http.get("/api/v1/commercial/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {
            "configured": False,
            "setup_status": "not_started",
            "side": None,
        }

    @pytest.mark.anyio
    async def test_status_when_completed(self, http, db, user_id):
        from app.repositories import commercial_profile_repo

        commercial_profile_repo.create(
            db, user_id=user_id, company_name="Acme", setup_status="completed"
        )
        db.commit()
        resp = await http.get("/api/v1/commercial/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["configured"] is True
        assert body["setup_status"] == "completed"
        assert body["side"] == "purchasing"


# ---------------------------------------------------------------------------
# /profile
# ---------------------------------------------------------------------------


class TestProfileEndpoints:
    @pytest.mark.anyio
    async def test_get_404_when_missing(self, http):
        resp = await http.get("/api/v1/commercial/profile")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_put_creates_then_get_returns(self, http):
        put = await http.put(
            "/api/v1/commercial/profile",
            json={"company_name": "Acme", "side": "purchasing", "gc_name": "Jane"},
        )
        assert put.status_code == 200, put.text
        got = await http.get("/api/v1/commercial/profile")
        assert got.status_code == 200
        body = got.json()
        assert body["company_name"] == "Acme"
        assert body["gc_name"] == "Jane"
        assert body["side"] == "purchasing"

    @pytest.mark.anyio
    async def test_put_partial_update_preserves_other_fields(self, http):
        await http.put(
            "/api/v1/commercial/profile",
            json={"company_name": "Acme", "gc_name": "Jane"},
        )
        await http.put("/api/v1/commercial/profile", json={"gc_name": "Bob"})
        got = await http.get("/api/v1/commercial/profile")
        assert got.json()["company_name"] == "Acme"
        assert got.json()["gc_name"] == "Bob"


# ---------------------------------------------------------------------------
# /setup
# ---------------------------------------------------------------------------


class TestColdStartEndpoints:
    @pytest.mark.anyio
    async def test_initial_setup_status(self, http):
        resp = await http.get("/api/v1/commercial/setup/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["completed"] is False
        assert body["step"] == 0
        assert body["progress"] == 0.0

    @pytest.mark.anyio
    async def test_submit_step_advances(self, http):
        resp = await http.post(
            "/api/v1/commercial/setup",
            json={
                "step": 0,
                "answers": {"who_uses": "lawyer", "mode": "full"},
                "quick_mode": False,
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["step"] == 1
        assert body["completed"] is False

    @pytest.mark.anyio
    async def test_invalid_step_value_returns_422(self, http):
        # pydantic rejects step=5 before the route body runs
        resp = await http.post(
            "/api/v1/commercial/setup",
            json={"step": 5, "answers": {}},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_seed_files_path_traversal_rejected(self, http):
        resp = await http.post(
            "/api/v1/commercial/setup",
            json={
                "step": 4,
                "answers": {},
                "seed_files": ["../etc/passwd"],
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /reviews
# ---------------------------------------------------------------------------


class TestReviewEndpoints:
    @pytest.mark.anyio
    async def test_list_empty(self, http):
        resp = await http.get("/api/v1/commercial/reviews")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    @pytest.mark.anyio
    async def test_list_returns_history(self, http, db, user_id):
        from app.repositories import contract_review_repo

        for i in range(3):
            contract_review_repo.create(
                db,
                user_id=user_id,
                review_type="vendor",
                agreement_name=f"agr-{i}",
            )
        db.commit()

        resp = await http.get("/api/v1/commercial/reviews")
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

    @pytest.mark.anyio
    async def test_get_returns_review_detail(self, http, db, user_id):
        from app.repositories import contract_review_repo

        review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
        db.commit()
        resp = await http.get(f"/api/v1/commercial/reviews/{review.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == review.id

    @pytest.mark.anyio
    async def test_get_404_when_missing(self, http):
        resp = await http.get("/api/v1/commercial/reviews/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_get_blocks_cross_user(self, http, db, user_id):
        from app.db.models.user import User
        from app.repositories import contract_review_repo

        other = "00000000-0000-4000-8000-000000000030"
        db.add(User(id=other, email="o@test.local", hashed_password="x" * 60))
        db.flush()
        rev = contract_review_repo.create(db, user_id=other, review_type="vendor")
        db.commit()

        resp = await http.get(f"/api/v1/commercial/reviews/{rev.id}")
        # AuthorizationError → 403
        assert resp.status_code == 403
