"""Service/agent-level tests for the privacy-legal (个人信息保护) module."""

import json
from datetime import date, timedelta

import pytest

from app.agents.privacy.agent import (
    _PROMPT_BUILDERS,
    _SKILL_TOOLS,
    SKILL_REVIEW_TYPE,
    create_privacy_agent,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.repositories import privacy_profile_repo, privacy_review_repo
from app.schemas.privacy.cold_start import ColdStartRequest
from app.schemas.privacy.dsar import PrivacyDsarCreate, PrivacyDsarUpdate
from app.schemas.privacy.profile import PrivacyProfileUpdate
from app.services.privacy_cold_start_service import PrivacyColdStartService
from app.services.privacy_dsar_service import PrivacyDsarService
from app.services.privacy_profile_service import PrivacyProfileService
from app.tasks import privacy_policy_sweep_reminder


class TestColdStart:
    def test_quick_mode_completes_and_materializes_profile(self, db, user_id):
        svc = PrivacyColdStartService(db)
        res = None
        for step in (0, 1, 5):
            res = svc.submit_step(
                user_id,
                ColdStartRequest(
                    step=step,
                    quick_mode=True,
                    answers={"user_role": "attorney"} if step == 0 else {},
                ),
            )
        assert res is not None and res.completed is True
        profile = PrivacyProfileService(db).get_my_profile(user_id)
        assert profile.setup_status == "completed"
        assert profile.setup_depth == "quick"

    def test_invalid_step_for_depth_raises(self, db, user_id):
        svc = PrivacyColdStartService(db)
        with pytest.raises(ValidationError):
            svc.submit_step(user_id, ColdStartRequest(step=2, quick_mode=True))


class TestProfile:
    def test_get_missing_raises(self, db, user_id):
        with pytest.raises(NotFoundError):
            PrivacyProfileService(db).get_my_profile(user_id)

    def test_upsert_creates_then_updates_json_fields(self, db, user_id):
        svc = PrivacyProfileService(db)
        created = svc.upsert_my_profile(
            user_id,
            PrivacyProfileUpdate(regulatory_footprint=["个保法", "数据安全法"]),
        )
        assert json.loads(created.regulatory_footprint) == ["个保法", "数据安全法"]
        updated = svc.upsert_my_profile(
            user_id, PrivacyProfileUpdate(regulatory_footprint=["个保法", "网络安全法"])
        )
        assert json.loads(updated.regulatory_footprint) == ["个保法", "网络安全法"]


class TestReviewRepo:
    def test_prior_reviews_and_count_since(self, db, user_id):
        privacy_review_repo.create(
            db, user_id=user_id, review_type="triage", subject="位置功能", severity="high"
        )
        privacy_review_repo.create(
            db, user_id=user_id, review_type="policy_sweep", subject="处理规则扫描"
        )
        prior = privacy_review_repo.list_by_subject(db, user_id=user_id, subject="位置功能")
        assert len(prior) == 1
        assert prior[0].severity == "high"
        # count_since excludes the sweep output itself.
        n = privacy_review_repo.count_since(
            db, user_id=user_id, since=None, exclude_type="policy_sweep"
        )
        assert n == 1


class TestDsar:
    def test_create_defaults_received_date(self, db, user_id):
        svc = PrivacyDsarService(db)
        dsar = svc.create(
            user_id=user_id,
            data=PrivacyDsarCreate(request_types=["access", "delete"], data_subject_ref="u-001"),
        )
        assert dsar.date_received == date.today()
        assert json.loads(dsar.request_types) == ["access", "delete"]
        assert dsar.status == "received"

    def test_update_and_foreign_raises(self, db, user_id):
        svc = PrivacyDsarService(db)
        dsar = svc.create(user_id=user_id, data=PrivacyDsarCreate(request_types=["access"]))
        updated = svc.update(
            dsar.id,
            user_id=user_id,
            data=PrivacyDsarUpdate(status="responded", identity_verified=True),
        )
        assert updated.status == "responded"
        assert updated.identity_verified is True
        with pytest.raises(NotFoundError):
            svc.get_owned("nonexistent", user_id=user_id)


class TestPolicySweepReminder:
    def _completed_profile(self, db, user_id, last_sweep: date | None):
        output_config = (
            json.dumps({"last_policy_sweep": last_sweep.isoformat()}) if last_sweep else None
        )
        privacy_profile_repo.create(
            db, user_id=user_id, setup_status="completed", output_config=output_config
        )

    def test_writes_reminder_when_new_outputs(self, db, user_id):
        self._completed_profile(db, user_id, last_sweep=date.today() - timedelta(days=30))
        privacy_review_repo.create(db, user_id=user_id, review_type="pia", subject="新功能")
        written = privacy_policy_sweep_reminder.run(db)
        assert written == 1

    def test_no_reminder_when_not_configured(self, db, user_id):
        # Profile not completed → skipped entirely.
        privacy_review_repo.create(db, user_id=user_id, review_type="pia", subject="x")
        assert privacy_policy_sweep_reminder.run(db) == 0


class TestAgentFactory:
    def test_skill_registries_aligned(self):
        assert set(_PROMPT_BUILDERS) == set(_SKILL_TOOLS)
        assert set(_PROMPT_BUILDERS) == {
            "triage",
            "dpa",
            "pia",
            "gap",
            "dsar",
            "policy_sweep",
            "policy_query",
        }
        # dsar writes privacy_dsar (not privacy_reviews) so it has no review_type.
        assert set(SKILL_REVIEW_TYPE) == set(_PROMPT_BUILDERS) - {"dsar"}

    def test_unknown_skill_raises(self):
        with pytest.raises(ValueError, match="Unknown privacy-legal skill"):
            create_privacy_agent("nonsense")  # type: ignore[arg-type]
