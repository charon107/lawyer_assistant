"""Tests for `contract_deviation_repo`."""

from datetime import datetime, timedelta

from app.repositories import contract_deviation_repo as repo
from app.repositories import contract_review_repo as review_repo


def _make_review(db, user_id):
    return review_repo.create(db, user_id=user_id, review_type="vendor")


class TestCreate:
    def test_create_minimal_defaults_green(self, db, user_id):
        review = _make_review(db, user_id)
        dev = repo.create(db, user_id=user_id, review_id=review.id, clause_key="liability_cap")
        assert dev.id
        assert dev.clause_key == "liability_cap"
        assert dev.severity_legal == "green"
        assert dev.severity_commercial == "green"

    def test_create_with_fields(self, db, user_id):
        review = _make_review(db, user_id)
        dev = repo.create(
            db,
            user_id=user_id,
            review_id=review.id,
            clause_key="indemnity",
            clause_label="赔偿",
            playbook_position="互相赔偿",
            signed_position="单向赔偿",
            severity_legal="red",
            severity_commercial="orange",
            category="risk",
        )
        assert dev.clause_label == "赔偿"
        assert dev.severity_legal == "red"
        assert dev.category == "risk"


class TestListByReview:
    def test_list_by_review_orders_oldest_first(self, db, user_id):
        review = _make_review(db, user_id)
        d1 = repo.create(db, user_id=user_id, review_id=review.id, clause_key="a")
        d2 = repo.create(db, user_id=user_id, review_id=review.id, clause_key="b")
        base = datetime(2026, 5, 28, 12, 0, 0)
        d1.created_at = base
        d2.created_at = base + timedelta(seconds=1)
        db.flush()
        result = repo.list_by_review(db, review.id)
        assert [d.id for d in result] == [d1.id, d2.id]


class TestCountByClause:
    def test_count_by_clause_total(self, db, user_id):
        review = _make_review(db, user_id)
        for _ in range(3):
            repo.create(db, user_id=user_id, review_id=review.id, clause_key="liability_cap")
        repo.create(db, user_id=user_id, review_id=review.id, clause_key="indemnity")
        assert repo.count_by_clause(db, user_id=user_id, clause_key="liability_cap") == 3
        assert repo.count_by_clause(db, user_id=user_id, clause_key="indemnity") == 1

    def test_count_by_clause_respects_since_window(self, db, user_id):
        review = _make_review(db, user_id)
        old = repo.create(db, user_id=user_id, review_id=review.id, clause_key="liability_cap")
        recent = repo.create(db, user_id=user_id, review_id=review.id, clause_key="liability_cap")
        old.created_at = datetime(2024, 1, 1, 12, 0, 0)
        recent.created_at = datetime(2026, 5, 1, 12, 0, 0)
        db.flush()
        since = datetime(2025, 5, 30, 0, 0, 0)
        assert (
            repo.count_by_clause(db, user_id=user_id, clause_key="liability_cap", since=since) == 1
        )


class TestAggregateByClause:
    def test_aggregate_orders_by_count_desc(self, db, user_id):
        review = _make_review(db, user_id)
        for _ in range(3):
            repo.create(
                db,
                user_id=user_id,
                review_id=review.id,
                clause_key="liability_cap",
                clause_label="责任上限",
            )
        repo.create(
            db,
            user_id=user_id,
            review_id=review.id,
            clause_key="indemnity",
            clause_label="赔偿",
        )
        result = repo.aggregate_by_clause(db, user_id=user_id)
        assert result[0] == ("liability_cap", "责任上限", 3)
        assert result[1] == ("indemnity", "赔偿", 1)


class TestDelete:
    def test_delete(self, db, user_id):
        review = _make_review(db, user_id)
        dev = repo.create(db, user_id=user_id, review_id=review.id, clause_key="a")
        repo.delete(db, dev)
        assert repo.get_by_id(db, dev.id) is None

    def test_review_delete_cascades(self, db, user_id):
        review = _make_review(db, user_id)
        dev = repo.create(db, user_id=user_id, review_id=review.id, clause_key="a")
        review_repo.delete(db, review)
        # The DB-level ON DELETE CASCADE removes the child row. Expunge the
        # stale child from the identity map so the identity-map-first
        # `get_by_id` issues a fresh SELECT and sees the row is gone.
        db.expunge_all()
        assert repo.get_by_id(db, dev.id) is None
