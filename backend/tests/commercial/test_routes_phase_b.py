"""Integration tests for the Phase B commercial REST endpoints.

Covers the four new domains added in Track B4:

  /matters      — CRUD-ish (create / list / detail / update)
  /renewals     — register (server computes 3 deadline dates) / list / update
  /deviations   — read-only per-clause aggregation
  /proposals    — list / accept-dismiss

Same wiring approach as test_routes.py: override the DB session + current
user + the relevant service factories so the routes hit our in-memory
SQLite session and a fake authenticated user.
"""

from collections.abc import AsyncGenerator
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import (
    get_commercial_matter_service,
    get_contract_deviation_service,
    get_current_user,
    get_db_session,
    get_playbook_proposal_service,
    get_renewal_service,
)
from app.main import app
from app.services.commercial_matter_service import CommercialMatterService
from app.services.contract_deviation_service import ContractDeviationService
from app.services.playbook_proposal_service import PlaybookProposalService
from app.services.renewal_service import RenewalService


@pytest.fixture
def fake_user(db, user_id):
    return SimpleNamespace(id=user_id, email="test@local", is_active=True)


@pytest.fixture
async def http(db, fake_user) -> AsyncGenerator[AsyncClient, None]:
    def _db():
        yield db

    app.dependency_overrides[get_db_session] = _db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_commercial_matter_service] = lambda: CommercialMatterService(db)
    app.dependency_overrides[get_renewal_service] = lambda: RenewalService(db)
    app.dependency_overrides[get_contract_deviation_service] = lambda: ContractDeviationService(db)
    app.dependency_overrides[get_playbook_proposal_service] = lambda: PlaybookProposalService(db)

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


# ---------------------------------------------------------------------------
# /matters
# ---------------------------------------------------------------------------


class TestMatterEndpoints:
    @pytest.mark.anyio
    async def test_create_then_list(self, http):
        created = await http.post(
            "/api/v1/commercial/matters",
            json={"counterparty": "供应商 A", "matter_name": "2026 采购框架"},
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["counterparty"] == "供应商 A"
        assert body["status"] == "active"

        listing = await http.get("/api/v1/commercial/matters")
        assert listing.status_code == 200
        assert listing.json()["total"] == 1

    @pytest.mark.anyio
    async def test_get_detail(self, http):
        created = await http.post("/api/v1/commercial/matters", json={"counterparty": "X"})
        mid = created.json()["id"]
        got = await http.get(f"/api/v1/commercial/matters/{mid}")
        assert got.status_code == 200
        assert got.json()["id"] == mid

    @pytest.mark.anyio
    async def test_get_404_when_missing(self, http):
        resp = await http.get("/api/v1/commercial/matters/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_patch_updates_status(self, http):
        created = await http.post("/api/v1/commercial/matters", json={"counterparty": "X"})
        mid = created.json()["id"]
        patched = await http.patch(f"/api/v1/commercial/matters/{mid}", json={"status": "closed"})
        assert patched.status_code == 200
        assert patched.json()["status"] == "closed"

    @pytest.mark.anyio
    async def test_get_blocks_cross_user(self, http, db):
        from app.repositories import commercial_matter_repo

        other = _make_other_user(db, "40")
        m = commercial_matter_repo.create(db, user_id=other, counterparty="X")
        db.commit()
        resp = await http.get(f"/api/v1/commercial/matters/{m.id}")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# /renewals
# ---------------------------------------------------------------------------


class TestRenewalEndpoints:
    @pytest.mark.anyio
    async def test_register_computes_dates(self, http):
        resp = await http.post(
            "/api/v1/commercial/renewals",
            json={
                "counterparty": "供应商 A",
                "agreement_name": "SaaS 主协议",
                "effective_date": "2026-01-15",
                "term_months": 12,
                "notice_days": 60,
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        # Server fills the three computed deadline dates.
        assert body["cancel_by_calendar"] is not None
        assert body["cancel_by_effective"] is not None
        assert body["send_by_effective"] is not None

    @pytest.mark.anyio
    async def test_list_renewals(self, http):
        await http.post(
            "/api/v1/commercial/renewals",
            json={"effective_date": "2026-01-01"},
        )
        listing = await http.get("/api/v1/commercial/renewals")
        assert listing.status_code == 200
        assert listing.json()["total"] == 1

    @pytest.mark.anyio
    async def test_patch_decision(self, http):
        created = await http.post(
            "/api/v1/commercial/renewals",
            json={"effective_date": "2026-01-01"},
        )
        rid = created.json()["id"]
        patched = await http.patch(f"/api/v1/commercial/renewals/{rid}", json={"decision": "renew"})
        assert patched.status_code == 200
        assert patched.json()["decision"] == "renew"

    @pytest.mark.anyio
    async def test_patch_term_recomputes_dates(self, http):
        created = await http.post(
            "/api/v1/commercial/renewals",
            json={"effective_date": "2026-01-15", "term_months": 12, "notice_days": 30},
        )
        before = created.json()["cancel_by_calendar"]
        rid = created.json()["id"]
        patched = await http.patch(f"/api/v1/commercial/renewals/{rid}", json={"notice_days": 90})
        assert patched.status_code == 200
        assert patched.json()["cancel_by_calendar"] != before


# ---------------------------------------------------------------------------
# /deviations
# ---------------------------------------------------------------------------


class TestDeviationEndpoints:
    @pytest.mark.anyio
    async def test_clause_counts_aggregate(self, http, db, user_id):
        from app.repositories import contract_deviation_repo, contract_review_repo

        review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
        contract_deviation_repo.create(
            db,
            user_id=user_id,
            review_id=review.id,
            clause_key="liability_cap",
            clause_label="责任上限",
        )
        contract_deviation_repo.create(
            db,
            user_id=user_id,
            review_id=review.id,
            clause_key="liability_cap",
            clause_label="责任上限",
        )
        contract_deviation_repo.create(
            db, user_id=user_id, review_id=review.id, clause_key="data_processing"
        )
        db.commit()

        resp = await http.get("/api/v1/commercial/deviations")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2  # two distinct clauses
        as_dict = {c["clause_key"]: c["count"] for c in body["items"]}
        assert as_dict == {"liability_cap": 2, "data_processing": 1}
        # Most-frequent first.
        assert body["items"][0]["clause_key"] == "liability_cap"


# ---------------------------------------------------------------------------
# /proposals
# ---------------------------------------------------------------------------


class TestProposalEndpoints:
    @pytest.mark.anyio
    async def test_list_isolates_user(self, http, db, user_id):
        from app.repositories import playbook_proposal_repo

        playbook_proposal_repo.create(db, user_id=user_id, clause_key="liability_cap")
        other = _make_other_user(db, "41")
        playbook_proposal_repo.create(db, user_id=other, clause_key="liability_cap")
        db.commit()

        resp = await http.get("/api/v1/commercial/proposals")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    @pytest.mark.anyio
    async def test_patch_accept(self, http, db, user_id):
        from app.repositories import playbook_proposal_repo

        p = playbook_proposal_repo.create(db, user_id=user_id, clause_key="liability_cap")
        db.commit()
        patched = await http.patch(
            f"/api/v1/commercial/proposals/{p.id}", json={"status": "accepted"}
        )
        assert patched.status_code == 200
        assert patched.json()["status"] == "accepted"

    @pytest.mark.anyio
    async def test_patch_blocks_cross_user(self, http, db):
        from app.repositories import playbook_proposal_repo

        other = _make_other_user(db, "42")
        p = playbook_proposal_repo.create(db, user_id=other, clause_key="liability_cap")
        db.commit()
        patched = await http.patch(
            f"/api/v1/commercial/proposals/{p.id}", json={"status": "dismissed"}
        )
        assert patched.status_code == 403
