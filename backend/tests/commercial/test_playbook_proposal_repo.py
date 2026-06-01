"""Tests for `playbook_proposal_repo`."""

from datetime import datetime, timedelta

from app.repositories import playbook_proposal_repo as repo


class TestCreate:
    def test_create_minimal_defaults_pending(self, db, user_id):
        proposal = repo.create(db, user_id=user_id, clause_key="liability_cap")
        assert proposal.id
        assert proposal.clause_key == "liability_cap"
        assert proposal.deviation_count == 0
        assert proposal.status == "pending"

    def test_create_with_fields(self, db, user_id):
        proposal = repo.create(
            db,
            user_id=user_id,
            clause_key="indemnity",
            clause_label="赔偿",
            current_position="互相赔偿",
            proposed_position="单向赔偿",
            deviation_count=6,
            rationale="近 12 个月已偏离 6 次",
        )
        assert proposal.clause_label == "赔偿"
        assert proposal.current_position == "互相赔偿"
        assert proposal.proposed_position == "单向赔偿"
        assert proposal.deviation_count == 6
        assert proposal.rationale == "近 12 个月已偏离 6 次"


class TestGetPendingByClause:
    def test_returns_open_proposal(self, db, user_id):
        created = repo.create(db, user_id=user_id, clause_key="liability_cap")
        found = repo.get_pending_by_clause(db, user_id=user_id, clause_key="liability_cap")
        assert found is not None
        assert found.id == created.id

    def test_returns_none_when_no_pending(self, db, user_id):
        repo.create(db, user_id=user_id, clause_key="liability_cap", status="accepted")
        found = repo.get_pending_by_clause(db, user_id=user_id, clause_key="liability_cap")
        assert found is None

    def test_returns_none_for_other_clause(self, db, user_id):
        repo.create(db, user_id=user_id, clause_key="liability_cap")
        found = repo.get_pending_by_clause(db, user_id=user_id, clause_key="indemnity")
        assert found is None


class TestGetAndList:
    def test_get_by_id_missing(self, db):
        assert repo.get_by_id(db, "00000000-0000-0000-0000-000000000000") is None

    def test_list_by_user_pagination(self, db, user_id):
        for i in range(4):
            repo.create(db, user_id=user_id, clause_key=f"c-{i}")
        items, total = repo.list_by_user(db, user_id=user_id, skip=0, limit=2)
        assert total == 4
        assert len(items) == 2

    def test_list_orders_by_created_at_desc(self, db, user_id):
        a = repo.create(db, user_id=user_id, clause_key="a")
        b = repo.create(db, user_id=user_id, clause_key="b")
        base = datetime(2026, 5, 28, 12, 0, 0)
        a.created_at = base
        b.created_at = base + timedelta(seconds=1)
        db.flush()
        items, _ = repo.list_by_user(db, user_id=user_id)
        assert [p.id for p in items] == [b.id, a.id]


class TestListPending:
    def test_orders_by_deviation_count_desc(self, db, user_id):
        low = repo.create(db, user_id=user_id, clause_key="a", deviation_count=5)
        high = repo.create(db, user_id=user_id, clause_key="b", deviation_count=12)
        result = repo.list_pending(db, user_id=user_id)
        assert [p.id for p in result] == [high.id, low.id]

    def test_excludes_non_pending(self, db, user_id):
        pending = repo.create(db, user_id=user_id, clause_key="a")
        repo.create(db, user_id=user_id, clause_key="b", status="accepted")
        repo.create(db, user_id=user_id, clause_key="c", status="dismissed")
        result = repo.list_pending(db, user_id=user_id)
        assert [p.id for p in result] == [pending.id]

    def test_isolates_users(self, db, user_id):
        from app.db.models.user import User

        other_id = "00000000-0000-4000-8000-000000000004"
        db.add(User(id=other_id, email="other3@test.local", hashed_password="x" * 60))
        db.flush()
        repo.create(db, user_id=other_id, clause_key="a")
        result = repo.list_pending(db, user_id=user_id)
        assert result == []


class TestUpdate:
    def test_update_to_accepted(self, db, user_id):
        proposal = repo.create(db, user_id=user_id, clause_key="a")
        repo.update(db, proposal=proposal, status="accepted")
        assert proposal.status == "accepted"

    def test_update_partial_does_not_clobber(self, db, user_id):
        proposal = repo.create(db, user_id=user_id, clause_key="a", proposed_position="单向赔偿")
        repo.update(db, proposal=proposal, status="dismissed")
        assert proposal.status == "dismissed"
        assert proposal.proposed_position == "单向赔偿"


class TestDelete:
    def test_delete(self, db, user_id):
        proposal = repo.create(db, user_id=user_id, clause_key="a")
        repo.delete(db, proposal)
        assert repo.get_by_id(db, proposal.id) is None
