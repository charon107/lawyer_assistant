"""Tests for the weekly renewal-watcher task.

The watcher fans out per active user, finds pending renewals whose cancellation
deadline lands inside the 90-day horizon, and drops a `renewal_due` notification
carrying the urgency band. No LLM, fully deterministic from the stored dates.
"""

import json
from datetime import date, timedelta

from app.repositories import commercial_notification_repo as notif_repo
from app.repositories import renewal_registration_repo as renewal_repo
from app.tasks import renewal_watcher


def _make_renewal(db, user_id, *, cancel_by: date, counterparty: str, decision: str = "pending"):
    return renewal_repo.create(
        db,
        user_id=user_id,
        counterparty=counterparty,
        agreement_name=f"{counterparty}-MSA",
        effective_date=date(2026, 1, 1),
        term_months=12,
        notice_days=30,
        cancel_by_calendar=cancel_by,
        cancel_by_effective=cancel_by,
        send_by_effective=cancel_by,
        decision=decision,
    )


class TestRenewalWatcherRun:
    def test_creates_notification_for_upcoming_pending(self, db, user_id):
        today = date(2026, 6, 1)
        _make_renewal(db, user_id, cancel_by=today + timedelta(days=10), counterparty="供应商A")

        created = renewal_watcher.run(db, today=today)

        assert created == 1
        items, total = notif_repo.list_by_user(db, user_id=user_id)
        assert total == 1
        assert items[0].type == "renewal_due"
        payload = json.loads(items[0].payload_json)
        assert payload["counterparty"] == "供应商A"
        assert payload["days_left"] == 10
        assert payload["urgency"] == "red"

    def test_excludes_beyond_horizon(self, db, user_id):
        today = date(2026, 6, 1)
        # 120 days out -> green, beyond the 90-day horizon
        _make_renewal(db, user_id, cancel_by=today + timedelta(days=120), counterparty="远期")

        created = renewal_watcher.run(db, today=today)

        assert created == 0
        _, total = notif_repo.list_by_user(db, user_id=user_id)
        assert total == 0

    def test_excludes_already_decided(self, db, user_id):
        today = date(2026, 6, 1)
        _make_renewal(
            db,
            user_id,
            cancel_by=today + timedelta(days=10),
            counterparty="已决定",
            decision="terminate",
        )

        created = renewal_watcher.run(db, today=today)

        assert created == 0

    def test_urgency_bands(self, db, user_id):
        today = date(2026, 6, 1)
        _make_renewal(db, user_id, cancel_by=today + timedelta(days=5), counterparty="红")
        _make_renewal(db, user_id, cancel_by=today + timedelta(days=30), counterparty="橙")
        _make_renewal(db, user_id, cancel_by=today + timedelta(days=60), counterparty="黄")

        created = renewal_watcher.run(db, today=today)
        assert created == 3

        items, _ = notif_repo.list_by_user(db, user_id=user_id)
        buckets = {
            json.loads(i.payload_json)["counterparty"]: json.loads(i.payload_json)["urgency"]
            for i in items
        }
        assert buckets == {"红": "red", "橙": "orange", "黄": "yellow"}

    def test_isolates_users(self, db, user_id):
        from app.db.models.user import User

        other_id = "00000000-0000-4000-8000-0000000000bb"
        db.add(User(id=other_id, email="other-rw@test.local", hashed_password="x" * 60))
        db.flush()
        today = date(2026, 6, 1)
        _make_renewal(db, user_id, cancel_by=today + timedelta(days=10), counterparty="我的")
        _make_renewal(db, other_id, cancel_by=today + timedelta(days=10), counterparty="别人的")

        renewal_watcher.run(db, today=today)

        _, mine = notif_repo.list_by_user(db, user_id=user_id)
        _, theirs = notif_repo.list_by_user(db, user_id=other_id)
        assert mine == 1
        assert theirs == 1
