"""Tests for the playbook-monitor task.

When a single clause family has been deviated from ≥ threshold times inside the
rolling 12-month window, the monitor raises one pending playbook proposal (and a
notification) — unless an open proposal for that clause already exists. No LLM:
the proposal is a deterministic flag, the lawyer decides the new position.
"""

from app.repositories import commercial_notification_repo as notif_repo
from app.repositories import contract_deviation_repo as deviation_repo
from app.repositories import contract_review_repo as review_repo
from app.repositories import playbook_proposal_repo as proposal_repo
from app.tasks import playbook_monitor


def _deviate(db, user_id, clause_key, *, times, label=None):
    review = review_repo.create(db, user_id=user_id, review_type="vendor")
    for _ in range(times):
        deviation_repo.create(
            db,
            user_id=user_id,
            review_id=review.id,
            clause_key=clause_key,
            clause_label=label,
        )


class TestPlaybookMonitorRun:
    def test_creates_proposal_when_threshold_met(self, db, user_id):
        _deviate(db, user_id, "liability_cap", times=5, label="责任上限")

        created = playbook_monitor.run(db)

        assert created == 1
        pending = proposal_repo.list_pending(db, user_id=user_id)
        assert len(pending) == 1
        assert pending[0].clause_key == "liability_cap"
        assert pending[0].deviation_count == 5
        assert pending[0].proposed_position is None

        items, total = notif_repo.list_by_user(db, user_id=user_id)
        assert total == 1
        assert items[0].type == "playbook_proposal"

    def test_no_proposal_below_threshold(self, db, user_id):
        _deviate(db, user_id, "indemnity", times=4)

        created = playbook_monitor.run(db)

        assert created == 0
        assert proposal_repo.list_pending(db, user_id=user_id) == []

    def test_dedup_existing_pending_proposal(self, db, user_id):
        _deviate(db, user_id, "liability_cap", times=5)
        proposal_repo.create(
            db,
            user_id=user_id,
            clause_key="liability_cap",
            deviation_count=5,
        )

        created = playbook_monitor.run(db)

        assert created == 0
        assert len(proposal_repo.list_pending(db, user_id=user_id)) == 1

    def test_isolates_users(self, db, user_id):
        from app.db.models.user import User

        other_id = "00000000-0000-4000-8000-0000000000cc"
        db.add(User(id=other_id, email="other-pm@test.local", hashed_password="x" * 60))
        db.flush()
        _deviate(db, user_id, "liability_cap", times=5)
        _deviate(db, other_id, "liability_cap", times=5)

        created = playbook_monitor.run(db)

        assert created == 2
        assert len(proposal_repo.list_pending(db, user_id=user_id)) == 1
        assert len(proposal_repo.list_pending(db, user_id=other_id)) == 1
