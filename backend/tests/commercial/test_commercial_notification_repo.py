"""Tests for `commercial_notification_repo`."""

from datetime import datetime, timedelta

from app.repositories import commercial_notification_repo as repo


class TestCreate:
    def test_create_minimal_defaults_unread(self, db, user_id):
        notif = repo.create(db, user_id=user_id, type="renewal_alert")
        assert notif.id
        assert notif.type == "renewal_alert"
        assert notif.read is False
        assert notif.payload_json is None

    def test_create_with_payload(self, db, user_id):
        notif = repo.create(
            db,
            user_id=user_id,
            type="deal_debrief",
            title="上周成交复盘",
            payload_json='{"deviations": 3}',
        )
        assert notif.title == "上周成交复盘"
        assert notif.payload_json == '{"deviations": 3}'


class TestGetById:
    def test_get_by_id_missing(self, db):
        assert repo.get_by_id(db, "00000000-0000-0000-0000-000000000000") is None

    def test_get_by_id_found(self, db, user_id):
        created = repo.create(db, user_id=user_id, type="renewal_alert")
        found = repo.get_by_id(db, created.id)
        assert found is not None
        assert found.id == created.id


class TestListByUser:
    def test_pagination(self, db, user_id):
        for _ in range(4):
            repo.create(db, user_id=user_id, type="renewal_alert")
        items, total = repo.list_by_user(db, user_id=user_id, skip=0, limit=2)
        assert total == 4
        assert len(items) == 2

    def test_orders_by_created_at_desc(self, db, user_id):
        a = repo.create(db, user_id=user_id, type="a")
        b = repo.create(db, user_id=user_id, type="b")
        base = datetime(2026, 5, 28, 12, 0, 0)
        a.created_at = base
        b.created_at = base + timedelta(seconds=1)
        db.flush()
        items, _ = repo.list_by_user(db, user_id=user_id)
        assert [n.id for n in items] == [b.id, a.id]

    def test_unread_only_filter(self, db, user_id):
        unread = repo.create(db, user_id=user_id, type="a")
        read = repo.create(db, user_id=user_id, type="b")
        repo.mark_read(db, notification=read)
        items, total = repo.list_by_user(db, user_id=user_id, unread_only=True)
        assert total == 1
        assert [n.id for n in items] == [unread.id]

    def test_isolates_users(self, db, user_id):
        from app.db.models.user import User

        other_id = "00000000-0000-4000-8000-000000000009"
        db.add(User(id=other_id, email="other9@test.local", hashed_password="x" * 60))
        db.flush()
        repo.create(db, user_id=other_id, type="a")
        items, total = repo.list_by_user(db, user_id=user_id)
        assert total == 0
        assert items == []


class TestUnreadCount:
    def test_counts_only_unread_for_user(self, db, user_id):
        repo.create(db, user_id=user_id, type="a")
        read = repo.create(db, user_id=user_id, type="b")
        repo.mark_read(db, notification=read)
        assert repo.unread_count(db, user_id=user_id) == 1


class TestMarkRead:
    def test_mark_read(self, db, user_id):
        notif = repo.create(db, user_id=user_id, type="a")
        repo.mark_read(db, notification=notif)
        assert notif.read is True

    def test_mark_all_read(self, db, user_id):
        repo.create(db, user_id=user_id, type="a")
        repo.create(db, user_id=user_id, type="b")
        updated = repo.mark_all_read(db, user_id=user_id)
        assert updated == 2
        assert repo.unread_count(db, user_id=user_id) == 0


class TestDelete:
    def test_delete(self, db, user_id):
        notif = repo.create(db, user_id=user_id, type="a")
        repo.delete(db, notif)
        assert repo.get_by_id(db, notif.id) is None
