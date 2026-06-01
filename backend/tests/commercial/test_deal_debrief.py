"""Tests for the weekly deal-debrief task.

For each active user it recaps the past week's completed reviews — counts by
status and total deviations read straight from each review's stored
`result_json` (no LLM) — into one `deal_debrief` notification. After the recap
it runs the playbook-monitor so an over-deviated clause surfaces in the same run.
"""

import json
from datetime import datetime, timedelta

from app.repositories import commercial_notification_repo as notif_repo
from app.repositories import contract_deviation_repo as deviation_repo
from app.repositories import contract_review_repo as review_repo
from app.repositories import playbook_proposal_repo as proposal_repo
from app.tasks import deal_debrief

_NOW = datetime(2026, 6, 1, 10, 0, 0)


def _completed_review(db, user_id, *, status, created_at, deviations):
    review = review_repo.create(db, user_id=user_id, review_type="vendor")
    review_repo.update_result(
        db,
        review=review,
        result_status=status,
        result_summary="ok",
        result_json={
            "summary": "s",
            "deviations": deviations,
            "favorable_terms": [],
            "missing_terms": [],
        },
    )
    review.created_at = created_at
    db.flush()
    return review


class TestDealDebriefRun:
    def test_creates_debrief_notification(self, db, user_id):
        _completed_review(
            db,
            user_id,
            status="yellow",
            created_at=_NOW - timedelta(days=2),
            deviations=[{"clause_key": "liability_cap"}, {"clause_key": "indemnity"}],
        )
        _completed_review(
            db,
            user_id,
            status="green",
            created_at=_NOW - timedelta(days=1),
            deviations=[],
        )

        created = deal_debrief.run(db, now=_NOW)

        assert created == 1
        items, total = notif_repo.list_by_user(db, user_id=user_id)
        debrief = next(i for i in items if i.type == "deal_debrief")
        payload = json.loads(debrief.payload_json)
        assert payload["reviews_count"] == 2
        assert payload["deviation_count"] == 2
        assert payload["by_status"]["yellow"] == 1
        assert payload["by_status"]["green"] == 1

    def test_skips_user_with_no_completed_reviews_in_window(self, db, user_id):
        # completed, but 10 days ago -> outside the 7-day window
        _completed_review(
            db, user_id, status="green", created_at=_NOW - timedelta(days=10), deviations=[]
        )

        created = deal_debrief.run(db, now=_NOW)

        assert created == 0
        items, _ = notif_repo.list_by_user(db, user_id=user_id)
        assert [i for i in items if i.type == "deal_debrief"] == []

    def test_also_runs_playbook_monitor(self, db, user_id):
        # 5 deviations on one clause should trip the playbook monitor even with
        # no completed reviews to recap.
        review = review_repo.create(db, user_id=user_id, review_type="vendor")
        for _ in range(5):
            deviation_repo.create(
                db, user_id=user_id, review_id=review.id, clause_key="liability_cap"
            )

        deal_debrief.run(db, now=_NOW)

        assert len(proposal_repo.list_pending(db, user_id=user_id)) == 1
