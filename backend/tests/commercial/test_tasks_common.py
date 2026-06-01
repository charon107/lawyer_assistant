"""Tests for `app.tasks._common` shared helpers.

The scheduled commercial tasks fan out per active user; `iter_active_user_ids`
is the single source of that user set so the three tasks stay consistent.
"""

from app.db.models.user import User
from app.tasks import _common


class TestIterActiveUserIds:
    def test_returns_active_user(self, db, user_id):
        ids = _common.iter_active_user_ids(db)
        assert user_id in ids

    def test_excludes_inactive_users(self, db, user_id):
        inactive_id = "00000000-0000-4000-8000-0000000000aa"
        db.add(
            User(
                id=inactive_id,
                email="inactive@test.local",
                hashed_password="x" * 60,
                is_active=False,
            )
        )
        db.flush()
        ids = _common.iter_active_user_ids(db)
        assert user_id in ids
        assert inactive_id not in ids

    def test_returns_plain_list_of_str(self, db, user_id):
        ids = _common.iter_active_user_ids(db)
        assert isinstance(ids, list)
        assert all(isinstance(i, str) for i in ids)
