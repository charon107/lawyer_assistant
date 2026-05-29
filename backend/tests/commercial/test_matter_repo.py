"""Tests for `commercial_matter_repo`."""

from app.repositories import commercial_matter_repo as repo


class TestCreate:
    def test_create_minimal_defaults_active(self, db, user_id):
        matter = repo.create(db, user_id=user_id)
        assert matter.id
        assert matter.user_id == user_id
        assert matter.status == "active"

    def test_create_with_fields(self, db, user_id):
        matter = repo.create(
            db,
            user_id=user_id,
            counterparty="供应商 A",
            matter_name="云服务采购",
            agreement_type="saas",
            owner="张律师",
            notes="续约谈判中",
        )
        assert matter.counterparty == "供应商 A"
        assert matter.matter_name == "云服务采购"
        assert matter.agreement_type == "saas"
        assert matter.owner == "张律师"
        assert matter.notes == "续约谈判中"


class TestGetAndList:
    def test_get_by_id_existing(self, db, user_id):
        created = repo.create(db, user_id=user_id)
        fetched = repo.get_by_id(db, created.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_by_id_missing(self, db):
        assert repo.get_by_id(db, "00000000-0000-0000-0000-000000000000") is None

    def test_list_by_user_pagination(self, db, user_id):
        for i in range(5):
            repo.create(db, user_id=user_id, matter_name=f"m-{i}")
        items, total = repo.list_by_user(db, user_id=user_id, skip=0, limit=3)
        assert total == 5
        assert len(items) == 3

    def test_list_orders_by_created_at_desc(self, db, user_id):
        from datetime import datetime, timedelta

        a = repo.create(db, user_id=user_id, matter_name="a")
        b = repo.create(db, user_id=user_id, matter_name="b")
        c = repo.create(db, user_id=user_id, matter_name="c")
        base = datetime(2026, 5, 28, 12, 0, 0)
        a.created_at = base
        b.created_at = base + timedelta(seconds=1)
        c.created_at = base + timedelta(seconds=2)
        db.flush()

        items, _ = repo.list_by_user(db, user_id=user_id)
        assert [m.id for m in items] == [c.id, b.id, a.id]

    def test_list_isolates_users(self, db, user_id):
        from app.db.models.user import User

        other_id = "00000000-0000-4000-8000-000000000002"
        db.add(User(id=other_id, email="other@test.local", hashed_password="x" * 60))
        db.flush()
        repo.create(db, user_id=user_id)
        repo.create(db, user_id=other_id)
        items, total = repo.list_by_user(db, user_id=user_id)
        assert total == 1
        assert items[0].user_id == user_id


class TestUpdate:
    def test_update_partial_does_not_clobber(self, db, user_id):
        matter = repo.create(db, user_id=user_id, counterparty="A", status="active")
        repo.update(db, matter=matter, status="closed")
        assert matter.status == "closed"
        assert matter.counterparty == "A"  # untouched

    def test_update_multiple_fields(self, db, user_id):
        matter = repo.create(db, user_id=user_id)
        repo.update(db, matter=matter, counterparty="B", matter_name="新事项", owner="李律师")
        assert matter.counterparty == "B"
        assert matter.matter_name == "新事项"
        assert matter.owner == "李律师"


class TestDelete:
    def test_delete(self, db, user_id):
        matter = repo.create(db, user_id=user_id)
        repo.delete(db, matter)
        assert repo.get_by_id(db, matter.id) is None
