"""Tests for CommercialNotificationService.

The service backs the commercial dashboard's notification inbox: list (with an
unread badge count), mark one read, and mark all read. Per-user isolation is
enforced exactly like the other commercial services — a user can never read or
mutate another user's notifications.
"""

import pytest

from app.core.exceptions import AuthorizationError, NotFoundError
from app.repositories import commercial_notification_repo as notif_repo
from app.services.commercial_notification_service import CommercialNotificationService


@pytest.fixture
def service(db) -> CommercialNotificationService:
    return CommercialNotificationService(db)


class TestListMyNotifications:
    def test_returns_items_total_and_unread(self, service, db, user_id):
        notif_repo.create(db, user_id=user_id, type="renewal_due", title="a", read=False)
        notif_repo.create(db, user_id=user_id, type="deal_debrief", title="b", read=True)

        items, total, unread = service.list_my_notifications(user_id)

        assert total == 2
        assert unread == 1
        assert len(items) == 2

    def test_unread_only_filters(self, service, db, user_id):
        notif_repo.create(db, user_id=user_id, type="renewal_due", title="a", read=False)
        notif_repo.create(db, user_id=user_id, type="deal_debrief", title="b", read=True)

        items, total, unread = service.list_my_notifications(user_id, unread_only=True)

        assert total == 1
        assert unread == 1
        assert all(not i.read for i in items)

    def test_isolates_users(self, service, db, user_id):
        from app.db.models.user import User

        other_id = "00000000-0000-4000-8000-0000000000dd"
        db.add(User(id=other_id, email="other-notif@test.local", hashed_password="x" * 60))
        db.flush()
        notif_repo.create(db, user_id=other_id, type="renewal_due", title="theirs", read=False)

        items, total, unread = service.list_my_notifications(user_id)

        assert total == 0
        assert unread == 0
        assert items == []


class TestUnreadCount:
    def test_counts_only_unread(self, service, db, user_id):
        notif_repo.create(db, user_id=user_id, type="renewal_due", read=False)
        notif_repo.create(db, user_id=user_id, type="renewal_due", read=False)
        notif_repo.create(db, user_id=user_id, type="renewal_due", read=True)

        assert service.unread_count(user_id) == 2


class TestMarkRead:
    def test_marks_owned_notification_read(self, service, db, user_id):
        n = notif_repo.create(db, user_id=user_id, type="renewal_due", read=False)

        updated = service.mark_read(user_id, n.id)

        assert updated.read is True

    def test_missing_notification_raises_not_found(self, service, user_id):
        with pytest.raises(NotFoundError):
            service.mark_read(user_id, "00000000-0000-4000-8000-000000000404")

    def test_other_users_notification_raises_authorization(self, service, db, user_id):
        from app.db.models.user import User

        other_id = "00000000-0000-4000-8000-0000000000ee"
        db.add(User(id=other_id, email="other-mark@test.local", hashed_password="x" * 60))
        db.flush()
        n = notif_repo.create(db, user_id=other_id, type="renewal_due", read=False)

        with pytest.raises(AuthorizationError):
            service.mark_read(user_id, n.id)


class TestMarkAllRead:
    def test_marks_all_unread_and_returns_count(self, service, db, user_id):
        notif_repo.create(db, user_id=user_id, type="renewal_due", read=False)
        notif_repo.create(db, user_id=user_id, type="deal_debrief", read=False)
        notif_repo.create(db, user_id=user_id, type="renewal_due", read=True)

        count = service.mark_all_read(user_id)

        assert count == 2
        assert service.unread_count(user_id) == 0
