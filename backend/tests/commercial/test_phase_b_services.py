"""Tests for the Phase B service layer: matters + renewals.

Run against a real in-memory SQLite session (see conftest) so we exercise
ownership isolation and the renewal-date computation end to end.

The renewal service is the interesting one: it must fill the three computed
deadline dates (cancel_by_calendar / cancel_by_effective / send_by_effective)
via `renewal_calc` before persisting, and recompute them when the term inputs
change on update.
"""

from datetime import date

import pytest

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.user import User
from app.repositories import contract_deviation_repo, playbook_proposal_repo
from app.schemas.commercial.matter import (
    CommercialMatterCreate,
    CommercialMatterUpdate,
)
from app.schemas.commercial.proposal import PlaybookProposalUpdate
from app.schemas.commercial.renewal import (
    RenewalRegistrationCreate,
    RenewalRegistrationUpdate,
)
from app.services import renewal_calc
from app.services.commercial_matter_service import CommercialMatterService
from app.services.contract_deviation_service import ContractDeviationService
from app.services.playbook_proposal_service import PlaybookProposalService
from app.services.renewal_service import RenewalService


def _make_user(db, user_id_suffix: str) -> str:
    """Create a throwaway second user and return its id."""
    other = f"00000000-0000-4000-8000-0000000000{user_id_suffix}"
    db.add(User(id=other, email=f"{user_id_suffix}@test.local", hashed_password="x" * 60))
    db.flush()
    return other


# ---------------------------------------------------------------------------
# CommercialMatterService
# ---------------------------------------------------------------------------


class TestMatterService:
    def test_create_matter_persists_fields(self, db, user_id):
        svc = CommercialMatterService(db)
        matter = svc.create_matter(
            user_id,
            CommercialMatterCreate(
                counterparty="供应商 A",
                matter_name="2026 采购框架",
                agreement_type="vendor",
            ),
        )
        assert matter.id
        assert matter.user_id == user_id
        assert matter.counterparty == "供应商 A"
        assert matter.status == "active"

    def test_create_matter_ignores_forged_user_id(self, db, user_id):
        other = _make_user(db, "31")
        svc = CommercialMatterService(db)
        body = CommercialMatterCreate(counterparty="LegitCo")
        forged = body.model_copy(update={"user_id": other})  # type: ignore[arg-type]
        matter = svc.create_matter(user_id, forged)  # type: ignore[arg-type]
        assert matter.user_id == user_id

    def test_get_my_matter_raises_not_found(self, db, user_id):
        svc = CommercialMatterService(db)
        with pytest.raises(NotFoundError):
            svc.get_my_matter(user_id, "00000000-0000-0000-0000-000000000000")

    def test_get_my_matter_blocks_cross_user(self, db, user_id):
        other = _make_user(db, "32")
        other_svc = CommercialMatterService(db)
        other_matter = other_svc.create_matter(other, CommercialMatterCreate(counterparty="X"))

        svc = CommercialMatterService(db)
        with pytest.raises(AuthorizationError):
            svc.get_my_matter(user_id, other_matter.id)

    def test_list_my_matters_isolates_user(self, db, user_id):
        svc = CommercialMatterService(db)
        for i in range(3):
            svc.create_matter(user_id, CommercialMatterCreate(counterparty=f"C{i}"))
        items, total = svc.list_my_matters(user_id)
        assert total == 3
        assert all(m.user_id == user_id for m in items)

    def test_update_my_matter_partial(self, db, user_id):
        svc = CommercialMatterService(db)
        matter = svc.create_matter(user_id, CommercialMatterCreate(counterparty="供应商 A"))
        updated = svc.update_my_matter(
            user_id,
            matter.id,
            CommercialMatterUpdate(status="closed"),
        )
        assert updated.status == "closed"
        assert updated.counterparty == "供应商 A"  # untouched

    def test_update_my_matter_blocks_cross_user(self, db, user_id):
        other = _make_user(db, "33")
        other_svc = CommercialMatterService(db)
        other_matter = other_svc.create_matter(other, CommercialMatterCreate(counterparty="X"))

        svc = CommercialMatterService(db)
        with pytest.raises(AuthorizationError):
            svc.update_my_matter(user_id, other_matter.id, CommercialMatterUpdate(status="closed"))


# ---------------------------------------------------------------------------
# RenewalService
# ---------------------------------------------------------------------------


class TestRenewalService:
    def test_register_computes_three_dates(self, db, user_id):
        svc = RenewalService(db)
        eff = date(2026, 1, 15)
        reg = svc.register_renewal(
            user_id,
            RenewalRegistrationCreate(
                counterparty="供应商 A",
                agreement_name="SaaS 主协议",
                effective_date=eff,
                term_months=12,
                notice_days=60,
            ),
        )
        assert reg.id
        assert reg.user_id == user_id
        # The three dates must match the pure-function output.
        assert reg.cancel_by_calendar == renewal_calc.cancel_by_calendar(eff, 12, 60)
        assert reg.cancel_by_effective == renewal_calc.cancel_by_effective(eff, 12, 60)
        assert reg.send_by_effective == renewal_calc.send_by_effective(eff, 12, 60)

    def test_register_ignores_forged_user_id(self, db, user_id):
        other = _make_user(db, "34")
        svc = RenewalService(db)
        body = RenewalRegistrationCreate(effective_date=date(2026, 1, 1))
        forged = body.model_copy(update={"user_id": other})  # type: ignore[arg-type]
        reg = svc.register_renewal(user_id, forged)  # type: ignore[arg-type]
        assert reg.user_id == user_id

    def test_list_my_renewals_isolates_user(self, db, user_id):
        svc = RenewalService(db)
        for _ in range(2):
            svc.register_renewal(
                user_id, RenewalRegistrationCreate(effective_date=date(2026, 1, 1))
            )
        items, total = svc.list_my_renewals(user_id)
        assert total == 2
        assert all(r.user_id == user_id for r in items)

    def test_update_recomputes_dates_when_term_changes(self, db, user_id):
        svc = RenewalService(db)
        eff = date(2026, 1, 15)
        reg = svc.register_renewal(
            user_id,
            RenewalRegistrationCreate(effective_date=eff, term_months=12, notice_days=30),
        )
        # Change notice_days → all three dates must shift.
        updated = svc.update_my_renewal(
            user_id,
            reg.id,
            RenewalRegistrationUpdate(notice_days=90),
        )
        assert updated.cancel_by_calendar == renewal_calc.cancel_by_calendar(eff, 12, 90)
        assert updated.cancel_by_effective == renewal_calc.cancel_by_effective(eff, 12, 90)
        assert updated.send_by_effective == renewal_calc.send_by_effective(eff, 12, 90)

    def test_update_decision_does_not_disturb_dates(self, db, user_id):
        svc = RenewalService(db)
        eff = date(2026, 1, 15)
        reg = svc.register_renewal(
            user_id,
            RenewalRegistrationCreate(effective_date=eff, term_months=12, notice_days=30),
        )
        before = reg.cancel_by_calendar
        updated = svc.update_my_renewal(
            user_id,
            reg.id,
            RenewalRegistrationUpdate(decision="renew"),
        )
        assert updated.decision == "renew"
        assert updated.cancel_by_calendar == before

    def test_update_blocks_cross_user(self, db, user_id):
        other = _make_user(db, "35")
        other_svc = RenewalService(db)
        other_reg = other_svc.register_renewal(
            other, RenewalRegistrationCreate(effective_date=date(2026, 1, 1))
        )
        svc = RenewalService(db)
        with pytest.raises(AuthorizationError):
            svc.update_my_renewal(
                user_id, other_reg.id, RenewalRegistrationUpdate(decision="renew")
            )


# ---------------------------------------------------------------------------
# ContractDeviationService (read-only, aggregated)
# ---------------------------------------------------------------------------


def _make_review(db, user_id: str) -> str:
    """Create a contract-review shell and return its id (deviations FK it)."""
    from app.repositories import contract_review_repo

    review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
    return review.id


class TestDeviationService:
    def test_clause_counts_aggregate_and_isolate(self, db, user_id):
        review = _make_review(db, user_id)
        # liability_cap x2, data_processing x1 for our user.
        contract_deviation_repo.create(
            db,
            user_id=user_id,
            review_id=review,
            clause_key="liability_cap",
            clause_label="责任上限",
        )
        contract_deviation_repo.create(
            db,
            user_id=user_id,
            review_id=review,
            clause_key="liability_cap",
            clause_label="责任上限",
        )
        contract_deviation_repo.create(
            db, user_id=user_id, review_id=review, clause_key="data_processing"
        )
        # Another user's deviation must not leak in.
        other = _make_user(db, "36")
        other_review = _make_review(db, other)
        contract_deviation_repo.create(
            db, user_id=other, review_id=other_review, clause_key="liability_cap"
        )

        svc = ContractDeviationService(db)
        counts = svc.list_clause_counts(user_id)
        as_dict = {c.clause_key: c.count for c in counts}
        assert as_dict == {"liability_cap": 2, "data_processing": 1}
        # Most-frequent first.
        assert counts[0].clause_key == "liability_cap"
        assert counts[0].clause_label == "责任上限"


# ---------------------------------------------------------------------------
# PlaybookProposalService (read + accept/dismiss)
# ---------------------------------------------------------------------------


class TestProposalService:
    def test_list_my_proposals_isolates_user(self, db, user_id):
        playbook_proposal_repo.create(db, user_id=user_id, clause_key="liability_cap")
        other = _make_user(db, "37")
        playbook_proposal_repo.create(db, user_id=other, clause_key="liability_cap")

        svc = PlaybookProposalService(db)
        items, total = svc.list_my_proposals(user_id)
        assert total == 1
        assert all(p.user_id == user_id for p in items)

    def test_update_proposal_accept(self, db, user_id):
        proposal = playbook_proposal_repo.create(db, user_id=user_id, clause_key="liability_cap")
        svc = PlaybookProposalService(db)
        updated = svc.update_my_proposal(
            user_id, proposal.id, PlaybookProposalUpdate(status="accepted")
        )
        assert updated.status == "accepted"

    def test_update_proposal_blocks_cross_user(self, db, user_id):
        other = _make_user(db, "38")
        proposal = playbook_proposal_repo.create(db, user_id=other, clause_key="liability_cap")
        svc = PlaybookProposalService(db)
        with pytest.raises(AuthorizationError):
            svc.update_my_proposal(user_id, proposal.id, PlaybookProposalUpdate(status="dismissed"))

    def test_update_proposal_not_found(self, db, user_id):
        svc = PlaybookProposalService(db)
        with pytest.raises(NotFoundError):
            svc.update_my_proposal(
                user_id,
                "00000000-0000-0000-0000-000000000000",
                PlaybookProposalUpdate(status="accepted"),
            )
