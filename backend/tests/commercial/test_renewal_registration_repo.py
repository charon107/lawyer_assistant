"""Tests for `renewal_registration_repo`."""

from datetime import date

from app.repositories import commercial_matter_repo as matter_repo
from app.repositories import renewal_registration_repo as repo


class TestCreate:
    def test_create_minimal(self, db, user_id):
        reg = repo.create(db, user_id=user_id, effective_date=date(2026, 1, 1))
        assert reg.id
        assert reg.user_id == user_id
        assert reg.effective_date == date(2026, 1, 1)
        assert reg.term_months == 12
        assert reg.auto_renew is False
        assert reg.notice_days == 0
        assert reg.decision == "pending"

    def test_create_with_computed_dates_and_matter(self, db, user_id):
        matter = matter_repo.create(db, user_id=user_id)
        reg = repo.create(
            db,
            user_id=user_id,
            matter_id=matter.id,
            counterparty="供应商 A",
            agreement_name="MSA-2026",
            effective_date=date(2026, 1, 1),
            term_months=24,
            auto_renew=True,
            notice_days=60,
            cancel_by_calendar=date(2027, 11, 2),
            cancel_by_effective=date(2027, 11, 2),
            send_by_effective=date(2027, 11, 2),
        )
        assert reg.matter_id == matter.id
        assert reg.auto_renew is True
        assert reg.cancel_by_calendar == date(2027, 11, 2)


class TestGetAndList:
    def test_get_by_id_missing(self, db):
        assert repo.get_by_id(db, "00000000-0000-0000-0000-000000000000") is None

    def test_list_by_user_pagination(self, db, user_id):
        for _ in range(4):
            repo.create(db, user_id=user_id, effective_date=date(2026, 1, 1))
        items, total = repo.list_by_user(db, user_id=user_id, skip=0, limit=2)
        assert total == 4
        assert len(items) == 2


class TestListUpcoming:
    def test_returns_only_pending_before_cutoff_sorted(self, db, user_id):
        # Soonest deadline, pending — included.
        soon = repo.create(
            db,
            user_id=user_id,
            effective_date=date(2026, 1, 1),
            cancel_by_calendar=date(2026, 6, 1),
        )
        # Later but still before cutoff, pending — included, after `soon`.
        later = repo.create(
            db,
            user_id=user_id,
            effective_date=date(2026, 1, 1),
            cancel_by_calendar=date(2026, 6, 20),
        )
        # Past cutoff — excluded.
        repo.create(
            db,
            user_id=user_id,
            effective_date=date(2026, 1, 1),
            cancel_by_calendar=date(2026, 9, 1),
        )
        # No computed deadline — excluded.
        repo.create(db, user_id=user_id, effective_date=date(2026, 1, 1))
        # Already decided — excluded even though deadline is near.
        repo.create(
            db,
            user_id=user_id,
            effective_date=date(2026, 1, 1),
            cancel_by_calendar=date(2026, 5, 1),
            decision="renew",
        )

        result = repo.list_upcoming(db, user_id=user_id, before_date=date(2026, 6, 30))
        assert [r.id for r in result] == [soon.id, later.id]

    def test_isolates_users(self, db, user_id):
        from app.db.models.user import User

        other_id = "00000000-0000-4000-8000-000000000003"
        db.add(User(id=other_id, email="other2@test.local", hashed_password="x" * 60))
        db.flush()
        repo.create(
            db,
            user_id=other_id,
            effective_date=date(2026, 1, 1),
            cancel_by_calendar=date(2026, 6, 1),
        )
        result = repo.list_upcoming(db, user_id=user_id, before_date=date(2026, 12, 31))
        assert result == []


class TestUpdate:
    def test_update_decision(self, db, user_id):
        reg = repo.create(db, user_id=user_id, effective_date=date(2026, 1, 1))
        repo.update(db, registration=reg, decision="terminate", notes="不再续约")
        assert reg.decision == "terminate"
        assert reg.notes == "不再续约"

    def test_update_partial_does_not_clobber(self, db, user_id):
        reg = repo.create(db, user_id=user_id, effective_date=date(2026, 1, 1), counterparty="A")
        repo.update(db, registration=reg, term_months=36)
        assert reg.term_months == 36
        assert reg.counterparty == "A"


class TestDelete:
    def test_delete(self, db, user_id):
        reg = repo.create(db, user_id=user_id, effective_date=date(2026, 1, 1))
        repo.delete(db, reg)
        assert repo.get_by_id(db, reg.id) is None

    def test_matter_delete_cascades(self, db, user_id):
        matter = matter_repo.create(db, user_id=user_id)
        reg = repo.create(db, user_id=user_id, matter_id=matter.id, effective_date=date(2026, 1, 1))
        matter_repo.delete(db, matter)
        # DB-level ON DELETE CASCADE removes the child row. Expunge the stale
        # child from the identity map so the identity-map-first `get_by_id`
        # issues a fresh SELECT and sees the row is gone.
        db.expunge_all()
        assert repo.get_by_id(db, reg.id) is None
