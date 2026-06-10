"""Service/agent-level tests for the ip-legal (知识产权) module."""

import json
from datetime import date, timedelta

import pytest

from app.agents.ip.agent import (
    _LAW_TOOL_SKILLS,
    _PROMPT_BUILDERS,
    _SKILL_TOOLS,
    SKILL_REVIEW_TYPE,
    create_ip_agent,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.repositories import ip_portfolio_repo, ip_profile_repo, ip_review_repo
from app.schemas.ip.cold_start import ColdStartRequest
from app.schemas.ip.enforcement import IpEnforcementCreate, IpEnforcementUpdate
from app.schemas.ip.profile import IpProfileUpdate
from app.services.ip_cold_start_service import IpColdStartService
from app.services.ip_enforcement_service import IpEnforcementService
from app.services.ip_portfolio_service import IpPortfolioService
from app.services.ip_profile_service import IpProfileService
from app.tasks import ip_deadline_rules, ip_renewal_watcher


class TestColdStart:
    def test_quick_mode_completes_and_materializes_profile(self, db, user_id):
        svc = IpColdStartService(db)
        res = None
        for step in (0, 1, 5):
            res = svc.submit_step(
                user_id,
                ColdStartRequest(
                    step=step,
                    quick_mode=True,
                    answers={"user_role": "patent_agent"} if step == 0 else {},
                ),
            )
        assert res is not None and res.completed is True
        profile = IpProfileService(db).get_my_profile(user_id)
        assert profile.setup_status == "completed"
        assert profile.setup_depth == "quick"
        assert profile.user_role == "patent_agent"

    def test_invalid_step_for_depth_raises(self, db, user_id):
        svc = IpColdStartService(db)
        with pytest.raises(ValidationError):
            svc.submit_step(user_id, ColdStartRequest(step=2, quick_mode=True))


class TestProfile:
    def test_get_missing_raises(self, db, user_id):
        with pytest.raises(NotFoundError):
            IpProfileService(db).get_my_profile(user_id)

    def test_upsert_creates_then_updates_json_fields(self, db, user_id):
        svc = IpProfileService(db)
        created = svc.upsert_my_profile(user_id, IpProfileUpdate(ip_scope=["商标", "专利"]))
        assert json.loads(created.ip_scope) == ["商标", "专利"]
        updated = svc.upsert_my_profile(user_id, IpProfileUpdate(ip_scope=["商标", "著作权"]))
        assert json.loads(updated.ip_scope) == ["商标", "著作权"]


class TestReviewRepo:
    def test_prior_reviews_lookup(self, db, user_id):
        ip_review_repo.create(
            db, user_id=user_id, review_type="clearance", subject="超级品牌", severity="high"
        )
        ip_review_repo.create(
            db, user_id=user_id, review_type="infringement", subject="无关产品"
        )
        prior = ip_review_repo.list_by_subject(db, user_id=user_id, subject="超级品牌")
        assert len(prior) == 1
        assert prior[0].severity == "high"


class TestEnforcement:
    def test_counter_notice_seeds_15_working_day_clock(self, db, user_id):
        svc = IpEnforcementService(db)
        row = svc.create(
            user_id=user_id,
            data=IpEnforcementCreate(matter_type="takedown", mode="counter"),
        )
        assert row.response_deadline is not None
        assert row.response_deadline > date.today()

    def test_cease_desist_send_no_default_deadline(self, db, user_id):
        svc = IpEnforcementService(db)
        row = svc.create(
            user_id=user_id,
            data=IpEnforcementCreate(matter_type="cease_desist", mode="send"),
        )
        assert row.response_deadline is None
        assert row.status == "intake"

    def test_update_and_foreign_raises(self, db, user_id):
        svc = IpEnforcementService(db)
        row = svc.create(user_id=user_id, data=IpEnforcementCreate(matter_type="cease_desist"))
        updated = svc.update(
            row.id, user_id=user_id, data=IpEnforcementUpdate(status="gated", escalation_flag=True)
        )
        assert updated.status == "gated"
        assert updated.escalation_flag is True
        with pytest.raises(NotFoundError):
            svc.get_owned("nonexistent", user_id=user_id)


class TestPortfolioDeadlines:
    def test_trademark_renewal_within_window_is_due_soon(self, db, user_id):
        # Registered ~9.95 years ago → renewal due in ~3 weeks.
        reg = date.today() - timedelta(days=int(365.25 * 10) - 20)
        dl = ip_deadline_rules.compute_next_deadline(
            asset_type="trademark",
            jurisdiction="CN",
            status="registered",
            filing_date=None,
            registration_date=reg,
            grant_date=None,
        )
        assert dl.deadline_type == "商标续展"
        assert dl.status in {"due_soon", "grace"}

    def test_copyright_has_no_renewal(self, db, user_id):
        dl = ip_deadline_rules.compute_next_deadline(
            asset_type="copyright",
            jurisdiction="CN",
            status="registered",
            filing_date=None,
            registration_date=date.today(),
            grant_date=None,
        )
        assert dl.due_date is None

    def test_report_buckets_urgent_trademark(self, db, user_id):
        ip_portfolio_repo.create(
            db,
            user_id=user_id,
            asset_type="trademark",
            jurisdiction="CN",
            title="测试商标",
            status="registered",
            registration_date=date.today() - timedelta(days=int(365.25 * 10) - 10),
        )
        report = IpPortfolioService(db).report(user_id=user_id)
        buckets = report["buckets"]
        urgent = buckets["grace_lapsed"] + buckets["due_30"]
        assert len(urgent) == 1

    def test_copyright_excluded_from_all_buckets(self, db, user_id):
        # Copyright has no renewal cycle — it must not appear in any bucket
        # (regression: previously fell into the "unknown / data-missing" bucket).
        ip_portfolio_repo.create(
            db,
            user_id=user_id,
            asset_type="copyright",
            jurisdiction="CN",
            title="某作品",
            status="registered",
            registration_date=date.today() - timedelta(days=400),
        )
        report = IpPortfolioService(db).report(user_id=user_id)
        assert all(len(v) == 0 for v in report["buckets"].values())

    def test_patent_without_filing_date_is_unknown(self, db, user_id):
        # grant_date alone cannot place the term/fee schedule under CN law.
        dl = ip_deadline_rules.compute_next_deadline(
            asset_type="patent_invention",
            jurisdiction="CN",
            status="granted",
            filing_date=None,
            registration_date=None,
            grant_date=date(2010, 1, 1),
        )
        assert dl.status == "unknown"
        assert dl.due_date is None


class TestRenewalWatcher:
    def _completed_profile(self, db, user_id):
        ip_profile_repo.create(db, user_id=user_id, setup_status="completed")

    def test_writes_alert_when_deadline_in_window(self, db, user_id):
        self._completed_profile(db, user_id)
        ip_portfolio_repo.create(
            db,
            user_id=user_id,
            asset_type="trademark",
            jurisdiction="CN",
            title="到期商标",
            status="registered",
            registration_date=date.today() - timedelta(days=int(365.25 * 10) - 15),
        )
        written = ip_renewal_watcher.run(db)
        assert written == 1

    def test_no_alert_when_not_configured(self, db, user_id):
        ip_portfolio_repo.create(
            db, user_id=user_id, asset_type="trademark", registration_date=date.today()
        )
        assert ip_renewal_watcher.run(db) == 0


class TestAgentFactory:
    def test_skill_registries_aligned(self):
        assert set(_PROMPT_BUILDERS) == set(_SKILL_TOOLS)
        assert set(_PROMPT_BUILDERS) == {
            "clearance",
            "fto",
            "invention",
            "infringement",
            "ip_clause",
            "oss",
            "cease_desist",
            "takedown",
        }
        # cease_desist / takedown write ip_enforcement (not ip_reviews).
        assert set(SKILL_REVIEW_TYPE) == set(_PROMPT_BUILDERS) - {"cease_desist", "takedown"}
        # oss is the one analysis skill not wired to the law-research tools.
        assert "oss" not in _LAW_TOOL_SKILLS

    def test_unknown_skill_raises(self):
        with pytest.raises(ValueError, match="Unknown ip-legal skill"):
            create_ip_agent("nonsense")  # type: ignore[arg-type]
