"""Tests for `module_config_repo`."""

import json

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories import module_config_repo as repo


class TestUpsert:
    def test_upsert_inserts_when_absent(self, db, user_id):
        cfg = repo.upsert(
            db,
            user_id=user_id,
            module_name="commercial-legal",
            setup_status="in_progress",
            setup_data={"step": 1, "answers": {"company": "Acme"}},
        )
        assert cfg.id
        assert cfg.setup_status == "in_progress"
        assert json.loads(cfg.setup_data) == {"step": 1, "answers": {"company": "Acme"}}

    def test_upsert_updates_when_present(self, db, user_id):
        repo.upsert(
            db,
            user_id=user_id,
            module_name="commercial-legal",
            setup_status="in_progress",
            setup_data={"step": 1},
        )
        updated = repo.upsert(
            db,
            user_id=user_id,
            module_name="commercial-legal",
            setup_status="completed",
            setup_data={"step": 4, "answers": {}},
            config_content="# Final\n",
        )
        assert updated.setup_status == "completed"
        assert updated.config_content == "# Final\n"
        assert json.loads(updated.setup_data)["step"] == 4

    def test_upsert_partial_update_leaves_other_fields(self, db, user_id):
        repo.upsert(
            db,
            user_id=user_id,
            module_name="commercial-legal",
            setup_status="in_progress",
            setup_data={"step": 2},
            config_content="some content",
        )
        repo.upsert(
            db,
            user_id=user_id,
            module_name="commercial-legal",
            setup_status="completed",  # only this changes
        )
        cfg = repo.get(db, user_id=user_id, module_name="commercial-legal")
        assert cfg.setup_status == "completed"
        assert cfg.config_content == "some content"  # untouched

    def test_unique_per_user_module(self, db, user_id):
        repo.upsert(db, user_id=user_id, module_name="commercial-legal", setup_status="in_progress")
        db.commit()
        # Manually inserting a duplicate row should violate the
        # uq_module_configs_user_module constraint.
        from app.db.models.module_config import ModuleConfig

        db.add(ModuleConfig(user_id=user_id, module_name="commercial-legal"))
        with pytest.raises(IntegrityError):
            db.flush()

    def test_same_user_multiple_modules_allowed(self, db, user_id):
        repo.upsert(db, user_id=user_id, module_name="commercial-legal")
        repo.upsert(db, user_id=user_id, module_name="employment-legal")
        assert repo.get(db, user_id=user_id, module_name="commercial-legal") is not None
        assert repo.get(db, user_id=user_id, module_name="employment-legal") is not None


class TestGet:
    def test_get_missing(self, db, user_id):
        assert repo.get(db, user_id=user_id, module_name="commercial-legal") is None

    def test_get_existing(self, db, user_id):
        created = repo.upsert(
            db, user_id=user_id, module_name="commercial-legal", setup_status="in_progress"
        )
        fetched = repo.get(db, user_id=user_id, module_name="commercial-legal")
        assert fetched.id == created.id


class TestDelete:
    def test_delete_existing(self, db, user_id):
        repo.upsert(db, user_id=user_id, module_name="commercial-legal")
        repo.delete(db, user_id=user_id, module_name="commercial-legal")
        assert repo.get(db, user_id=user_id, module_name="commercial-legal") is None

    def test_delete_missing_returns_none(self, db, user_id):
        assert repo.delete(db, user_id=user_id, module_name="commercial-legal") is None
