"""Tests for `commercial_profile_repo`."""

import json

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories import commercial_profile_repo as repo
from app.schemas.commercial.playbook import EscalationRule, Playbook, PlaybookEntry


class TestCreate:
    def test_create_minimal_profile(self, db, user_id):
        profile = repo.create(db, user_id=user_id)
        assert profile.id
        assert profile.user_id == user_id
        assert profile.side == "purchasing"  # default
        assert profile.setup_status == "in_progress"  # default in repo

    def test_create_with_all_scalars(self, db, user_id):
        profile = repo.create(
            db,
            user_id=user_id,
            company_name="Acme Corp",
            entity_type="LLC",
            team_size="2-5",
            gc_name="Jane Doe",
            monthly_volume="20-50",
            side="sales",
            profile_content="# My profile\n",
            renewal_alert_channel="feishu",
            output_destination="email",
        )
        assert profile.company_name == "Acme Corp"
        assert profile.side == "sales"
        assert profile.profile_content == "# My profile\n"

    def test_create_serializes_playbook_object(self, db, user_id):
        pb = Playbook(
            side="purchasing",
            entries=[
                PlaybookEntry(clause_key="liability_cap", label="责任上限", standard="100%"),
            ],
        )
        profile = repo.create(db, user_id=user_id, playbook_purchasing=pb)
        # Stored as JSON text
        assert isinstance(profile.playbook_purchasing, str)
        decoded = json.loads(profile.playbook_purchasing)
        assert decoded["side"] == "purchasing"
        assert decoded["entries"][0]["clause_key"] == "liability_cap"

    def test_create_serializes_escalation_matrix_list(self, db, user_id):
        rules = [
            EscalationRule(min_severity="high", approver_role="GC", channel="feishu"),
            EscalationRule(min_severity="critical", approver_role="CEO"),
        ]
        profile = repo.create(db, user_id=user_id, escalation_matrix=rules)
        decoded = json.loads(profile.escalation_matrix)
        assert len(decoded) == 2
        assert decoded[0]["approver_role"] == "GC"

    def test_create_twice_for_same_user_violates_unique(self, db, user_id):
        repo.create(db, user_id=user_id)
        db.commit()
        with pytest.raises(IntegrityError):
            repo.create(db, user_id=user_id)


class TestGet:
    def test_get_existing(self, db, user_id):
        created = repo.create(db, user_id=user_id, company_name="X")
        fetched = repo.get_by_user_id(db, user_id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.company_name == "X"

    def test_get_missing_returns_none(self, db, user_id):
        assert repo.get_by_user_id(db, user_id) is None


class TestUpdate:
    def test_update_scalar_field(self, db, user_id):
        profile = repo.create(db, user_id=user_id, company_name="Old")
        repo.update(db, profile=profile, company_name="New")
        assert profile.company_name == "New"

    def test_update_does_not_overwrite_unspecified_fields(self, db, user_id):
        profile = repo.create(db, user_id=user_id, company_name="Acme", gc_name="Jane")
        repo.update(db, profile=profile, company_name="Beta")
        assert profile.company_name == "Beta"
        assert profile.gc_name == "Jane"  # untouched

    def test_update_setup_status(self, db, user_id):
        profile = repo.create(db, user_id=user_id)
        repo.update(db, profile=profile, setup_status="completed")
        assert profile.setup_status == "completed"

    def test_update_playbook_re_serializes(self, db, user_id):
        profile = repo.create(db, user_id=user_id)
        pb = Playbook(side="purchasing", entries=[])
        repo.update(db, profile=profile, playbook_purchasing=pb)
        assert json.loads(profile.playbook_purchasing) == {"side": "purchasing", "entries": []}


class TestDelete:
    def test_delete_existing(self, db, user_id):
        repo.create(db, user_id=user_id)
        deleted = repo.delete_by_user_id(db, user_id)
        assert deleted is not None
        assert repo.get_by_user_id(db, user_id) is None

    def test_delete_missing_returns_none(self, db, user_id):
        assert repo.delete_by_user_id(db, user_id) is None

    def test_delete_cascades_from_user(self, db, user_id):
        from app.db.models.user import User

        repo.create(db, user_id=user_id)
        # Removing the user should also remove the profile because the FK
        # is ON DELETE CASCADE and SQLite PRAGMA foreign_keys is ON.
        user = db.get(User, user_id)
        db.delete(user)
        db.flush()
        assert repo.get_by_user_id(db, user_id) is None
