"""Tests for the commercial-legal service layer.

Like the repository tests, these run against a real in-memory SQLite
session so we exercise constraint behavior and JSON round-trip.
"""

import pytest

from app.core.exceptions import AuthorizationError, NotFoundError
from app.repositories import commercial_profile_repo, contract_review_repo
from app.schemas.commercial.cold_start import ColdStartRequest
from app.schemas.commercial.playbook import EscalationRule, Playbook, PlaybookEntry
from app.schemas.commercial.profile import (
    CommercialProfileCreate,
    CommercialProfileUpdate,
)
from app.schemas.commercial.review import ContractReviewCreate
from app.services.cold_start_service import ColdStartService
from app.services.commercial_profile_service import CommercialProfileService
from app.services.contract_review_service import ContractReviewService

# ---------------------------------------------------------------------------
# CommercialProfileService
# ---------------------------------------------------------------------------


class TestProfileService:
    def test_get_my_profile_or_none_when_missing(self, db, user_id):
        svc = CommercialProfileService(db)
        assert svc.get_my_profile_or_none(user_id) is None

    def test_get_my_profile_raises_not_found(self, db, user_id):
        svc = CommercialProfileService(db)
        with pytest.raises(NotFoundError):
            svc.get_my_profile(user_id)

    def test_upsert_creates_on_first_call(self, db, user_id):
        svc = CommercialProfileService(db)
        profile = svc.upsert_my_profile(
            user_id,
            CommercialProfileCreate(
                company_name="Acme",
                side="purchasing",
                gc_name="Jane",
            ),
        )
        assert profile.id
        assert profile.company_name == "Acme"

    def test_upsert_updates_on_second_call(self, db, user_id):
        svc = CommercialProfileService(db)
        svc.upsert_my_profile(user_id, CommercialProfileCreate(company_name="Acme"))
        svc.upsert_my_profile(user_id, CommercialProfileUpdate(gc_name="Jane"))
        fetched = svc.get_my_profile(user_id)
        assert fetched.company_name == "Acme"  # untouched
        assert fetched.gc_name == "Jane"

    def test_upsert_ignores_user_id_in_payload(self, db, user_id):
        """Even if someone tries to put user_id in the body, we use the
        authenticated user_id arg only."""
        from app.db.models.user import User

        other = "00000000-0000-4000-8000-000000000020"
        db.add(User(id=other, email="o@test.local", hashed_password="x" * 60))
        db.flush()

        svc = CommercialProfileService(db)
        body = CommercialProfileCreate(company_name="LegitCo")
        # Sneak user_id into the dict-form payload via model_copy
        forged = body.model_copy(update={"user_id": other})  # type: ignore[arg-type]
        profile = svc.upsert_my_profile(user_id, forged)  # type: ignore[arg-type]
        assert profile.user_id == user_id  # not `other`


# ---------------------------------------------------------------------------
# ContractReviewService
# ---------------------------------------------------------------------------


class TestReviewService:
    def test_start_review_creates_in_progress_row(self, db, user_id):
        svc = ContractReviewService(db)
        review = svc.start_review(
            user_id,
            ContractReviewCreate(
                review_type="vendor",
                counterparty="供应商 A",
                annual_value=100000.0,
            ),
        )
        assert review.id
        assert review.result_status == "in_progress"
        assert review.counterparty == "供应商 A"

    def test_get_my_review_raises_not_found(self, db, user_id):
        svc = ContractReviewService(db)
        with pytest.raises(NotFoundError):
            svc.get_my_review(user_id, "00000000-0000-0000-0000-000000000000")

    def test_get_my_review_blocks_cross_user(self, db, user_id):
        from app.db.models.user import User

        other = "00000000-0000-4000-8000-000000000021"
        db.add(User(id=other, email="o2@test.local", hashed_password="x" * 60))
        db.flush()
        other_review = contract_review_repo.create(db, user_id=other, review_type="vendor")

        svc = ContractReviewService(db)
        with pytest.raises(AuthorizationError):
            svc.get_my_review(user_id, other_review.id)

    def test_list_my_reviews_isolates_user(self, db, user_id):
        svc = ContractReviewService(db)
        for _ in range(3):
            svc.start_review(user_id, ContractReviewCreate(review_type="vendor"))
        items, total = svc.list_my_reviews(user_id)
        assert total == 3
        assert all(r.user_id == user_id for r in items)


# ---------------------------------------------------------------------------
# ColdStartService
# ---------------------------------------------------------------------------


class TestColdStartService:
    def test_initial_progress_is_zero(self, db, user_id):
        svc = ColdStartService(db)
        resp = svc.get_progress(user_id)
        assert resp.completed is False
        assert resp.step == 0
        assert resp.progress == 0.0

    def test_submit_step_advances_progress(self, db, user_id):
        svc = ColdStartService(db)
        resp = svc.submit_step(
            user_id,
            ColdStartRequest(step=0, answers={"who_uses": "lawyer", "mode": "full"}),
        )
        assert resp.step == 1
        assert resp.progress == pytest.approx(0.2)
        assert resp.completed is False

    def test_resubmitting_earlier_step_preserves_later_state(self, db, user_id):
        svc = ColdStartService(db)
        svc.submit_step(user_id, ColdStartRequest(step=0, answers={"a": 1}))
        svc.submit_step(user_id, ColdStartRequest(step=1, answers={"b": 2}))
        # Re-submit step 0
        resp = svc.submit_step(user_id, ColdStartRequest(step=0, answers={"a": 99}))
        # step 1 answers must still be there
        assert "1" in resp.partial_config.get("steps", {})

    def test_final_step_materializes_profile(self, db, user_id):
        svc = ColdStartService(db)
        # Step 1: team
        svc.submit_step(
            user_id,
            ColdStartRequest(
                step=1,
                answers={
                    "company_name": "Acme",
                    "side": "purchasing",
                    "gc_name": "Jane",
                },
            ),
        )
        # Step 2: playbook
        pb = Playbook(
            side="purchasing",
            entries=[
                PlaybookEntry(clause_key="liability_cap", label="责任上限", standard="100%"),
            ],
        )
        svc.submit_step(
            user_id,
            ColdStartRequest(
                step=2,
                answers={"playbook_purchasing": pb.model_dump()},
            ),
        )
        # Step 3: escalation
        esc = [EscalationRule(min_severity="high", approver_role="GC")]
        svc.submit_step(
            user_id,
            ColdStartRequest(
                step=3,
                answers={"escalation_matrix": [e.model_dump() for e in esc]},
            ),
        )
        # Step 4 (final)
        resp = svc.submit_step(user_id, ColdStartRequest(step=4, answers={}))
        assert resp.completed is True

        profile = commercial_profile_repo.get_by_user_id(db, user_id)
        assert profile is not None
        assert profile.setup_status == "completed"
        assert profile.company_name == "Acme"
        assert profile.gc_name == "Jane"
        assert profile.playbook_purchasing is not None
        assert profile.escalation_matrix is not None

    # Note: pydantic schema constrains step to 0..4 so the service-layer
    # "invalid step" branch is unreachable from a real client; it stays
    # as defense-in-depth but isn't worth a unit test.
