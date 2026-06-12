"""Service / repo / task / agent-factory tests for the litigation-legal module.

Mirrors tests/ip/test_ip_flow.py. Covers the cold-start state machine, matter
service (incl. portfolio aggregation without N+1, non-lawyer advisory), event
repo helpers, demand/analysis services, the pure-arithmetic docket bucketing,
the docket-watcher run, and a C1 regression guard for the law tool.
"""

import asyncio
import inspect
import json
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.agents.litigation.agent import (
    _LAW_TOOL_SKILLS,
    _PROMPT_BUILDERS,
    _SKILL_TOOLS,
    SKILL_ANALYSIS_TYPE,
    create_litigation_agent,
)
from app.agents.litigation.deps import LitigationDeps
from app.agents.litigation.tools.law_tools import research_litigation_rules
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.repositories import (
    litigation_analysis_repo,
    litigation_matter_event_repo,
    litigation_matter_repo,
    litigation_notification_repo,
    litigation_profile_repo,
)
from app.schemas.litigation.cold_start import ColdStartRequest
from app.schemas.litigation.demand import LitigationDemandCreate
from app.schemas.litigation.matter import LitigationMatterCreate, LitigationMatterUpdate
from app.schemas.litigation.matter_event import LitigationMatterEventCreate
from app.schemas.litigation.profile import LitigationProfileUpdate
from app.services.litigation_analysis_service import LitigationAnalysisService
from app.services.litigation_cold_start_service import LitigationColdStartService
from app.services.litigation_demand_service import LitigationDemandService
from app.services.litigation_matter_service import LitigationMatterService
from app.services.litigation_profile_service import LitigationProfileService
from app.tasks import litigation_deadline_rules, litigation_docket_watcher


# --------------------------------------------------------------------------- #
# Cold-start state machine
# --------------------------------------------------------------------------- #
class TestColdStart:
    def test_quick_mode_completes_and_materializes_profile(self, db, user_id):
        svc = LitigationColdStartService(db)
        res = None
        for step in (0, 1, 4):  # QUICK_PLAN
            res = svc.submit_step(
                user_id,
                ColdStartRequest(
                    step=step,
                    quick_mode=True,
                    answers={"user_role": "lawyer", "practice_role": "企业法务"}
                    if step == 0
                    else {},
                ),
            )
        assert res is not None and res.completed is True
        profile = LitigationProfileService(db).get_my_profile(user_id)
        assert profile.setup_status == "completed"
        assert profile.setup_depth == "quick"
        assert profile.user_role == "lawyer"

    def test_invalid_step_for_depth_raises(self, db, user_id):
        svc = LitigationColdStartService(db)
        with pytest.raises(ValidationError):
            svc.submit_step(user_id, ColdStartRequest(step=2, quick_mode=True))


# --------------------------------------------------------------------------- #
# Profile service
# --------------------------------------------------------------------------- #
class TestProfile:
    def test_get_missing_raises(self, db, user_id):
        with pytest.raises(NotFoundError):
            LitigationProfileService(db).get_my_profile(user_id)

    def test_upsert_creates_then_updates(self, db, user_id):
        svc = LitigationProfileService(db)
        created = svc.upsert_my_profile(user_id, LitigationProfileUpdate(party_role="原告方"))
        assert created.party_role == "原告方"
        updated = svc.upsert_my_profile(user_id, LitigationProfileUpdate(party_role="被告方"))
        assert updated.party_role == "被告方"


# --------------------------------------------------------------------------- #
# Matter service
# --------------------------------------------------------------------------- #
class TestMatterService:
    def test_create_json_encodes_conflicts(self, db, user_id):
        svc = LitigationMatterService(db)
        m = svc.create(
            user_id=user_id,
            data=LitigationMatterCreate(
                case_name="某买卖合同纠纷",
                our_side="plaintiff",
                conflicts={"status": "cleared", "method": "法务部自查"},
            ),
        )
        assert json.loads(m.conflicts) == {"status": "cleared", "method": "法务部自查"}

    def test_get_owned_not_found_and_not_owned(self, db, user_id):
        svc = LitigationMatterService(db)
        with pytest.raises(NotFoundError):
            svc.get_owned("missing", user_id=user_id)
        mine = litigation_matter_repo.create(db, user_id=user_id, case_name="我的案件")
        with pytest.raises(AuthorizationError):
            svc.get_owned(mine.id, user_id="intruder")

    def test_update_records_status_change_event(self, db, user_id):
        svc = LitigationMatterService(db)
        m = svc.create(user_id=user_id, data=LitigationMatterCreate(case_name="案件A"))
        svc.update(m.id, user_id=user_id, data=LitigationMatterUpdate(status="settled"))
        events = litigation_matter_event_repo.list_by_matter(db, matter_id=m.id)
        assert any("状态变更" in (e.summary or "") for e in events)

    def test_close_lawyer_has_no_advisory(self, db, user_id):
        litigation_profile_repo.create(
            db, user_id=user_id, user_role="lawyer", setup_status="completed"
        )
        svc = LitigationMatterService(db)
        m = svc.create(user_id=user_id, data=LitigationMatterCreate(case_name="案件B"))
        closed = svc.close(m.id, user_id=user_id)
        assert closed.status == "closed" and closed.closed_date is not None
        events = litigation_matter_event_repo.list_by_matter(db, matter_id=m.id)
        closing = next(e for e in events if e.event_type == "closing")
        assert "非律师" not in (closing.summary or "")

    def test_close_non_lawyer_records_review_advisory(self, db, user_id):
        litigation_profile_repo.create(
            db, user_id=user_id, user_role="non_lawyer_without", setup_status="completed"
        )
        svc = LitigationMatterService(db)
        m = svc.create(user_id=user_id, data=LitigationMatterCreate(case_name="案件C"))
        svc.close(m.id, user_id=user_id)
        events = litigation_matter_event_repo.list_by_matter(db, matter_id=m.id)
        closing = next(e for e in events if e.event_type == "closing")
        assert "需执业律师审查" in (closing.summary or "")

    def test_add_deadline_event_updates_next_deadline(self, db, user_id):
        svc = LitigationMatterService(db)
        m = svc.create(user_id=user_id, data=LitigationMatterCreate(case_name="案件D"))
        due = date.today() + timedelta(days=10)
        svc.add_event(
            matter_id=m.id,
            user_id=user_id,
            data=LitigationMatterEventCreate(
                event_type="deadline", due_date=due, summary="举证期限届满"
            ),
        )
        refreshed = litigation_matter_repo.get_by_id(db, m.id)
        assert refreshed.next_deadline == due

    def test_portfolio_aggregates_and_flags_anomalies(self, db, user_id):
        svc = LitigationMatterService(db)
        svc.create(
            user_id=user_id,
            data=LitigationMatterCreate(case_name="高风险案", risk="严重", stage="庭审"),
        )
        svc.create(user_id=user_id, data=LitigationMatterCreate(case_name="无信息案"))
        report = svc.portfolio(user_id)
        assert report["total"] == 2
        assert report["active"] == 2
        assert report["by_risk"].get("严重") == 1
        assert report["anomalies"]["high_risk"] == 1
        # 两个案件都无事件 → no_events == 2
        assert report["anomalies"]["no_events"] == 2


# --------------------------------------------------------------------------- #
# Matter-event repo helpers (used by portfolio + docket)
# --------------------------------------------------------------------------- #
class TestMatterEventRepo:
    def test_deadline_and_latest_and_recent_helpers(self, db, user_id):
        m = litigation_matter_repo.create(db, user_id=user_id, case_name="案件E")
        old = date.today() - timedelta(days=120)
        recent = date.today() - timedelta(days=2)
        litigation_matter_event_repo.create(
            db, matter_id=m.id, user_id=user_id, event_type="procedure", event_date=old
        )
        litigation_matter_event_repo.create(
            db,
            matter_id=m.id,
            user_id=user_id,
            event_type="deadline",
            event_date=recent,
            due_date=date.today() + timedelta(days=5),
        )
        litigation_matter_event_repo.create(
            db,
            matter_id=m.id,
            user_id=user_id,
            event_type="substantive",
            event_date=recent,
            summary="一审判决已下",
        )

        deadlines = litigation_matter_event_repo.list_deadlines_by_user(db, user_id=user_id)
        assert len(deadlines) == 1

        latest = litigation_matter_event_repo.latest_event_date_by_matter(db, user_id=user_id)
        assert latest[m.id] == recent  # most recent, not the 120-day-old one

        changes = litigation_matter_event_repo.list_recent_status_changes_by_user(
            db, user_id=user_id, since=date.today() - timedelta(days=7)
        )
        # deadline excluded; old procedure excluded by date; substantive included
        assert [e.event_type for e in changes] == ["substantive"]


# --------------------------------------------------------------------------- #
# Demand + analysis services (ownership)
# --------------------------------------------------------------------------- #
class TestDemandAndAnalysis:
    def test_demand_create_and_ownership(self, db, user_id):
        svc = LitigationDemandService(db)
        d = svc.create(
            user_id=user_id,
            data=LitigationDemandCreate(demand_type="payment", mode="send", counterparty="某公司"),
        )
        assert svc.get_owned(d.id, user_id=user_id).id == d.id
        with pytest.raises((NotFoundError, AuthorizationError)):
            svc.get_owned(d.id, user_id="intruder")

    def test_analysis_list_and_ownership(self, db, user_id):
        litigation_analysis_repo.create(
            db, user_id=user_id, analysis_type="chronology", subject="案件X", status="final"
        )
        svc = LitigationAnalysisService(db)
        items, total = svc.list_analyses(user_id=user_id)
        assert total == 1 and items[0].analysis_type == "chronology"


# --------------------------------------------------------------------------- #
# Docket deadline bucketing (pure arithmetic, no LLM)
# --------------------------------------------------------------------------- #
class TestDeadlineRules:
    def _ev(self, days_from_now, status=None):
        return SimpleNamespace(
            id=f"e{days_from_now}",
            matter_id="m1",
            due_date=date.today() + timedelta(days=days_from_now),
            summary="x",
            deadline_status=status,
        )

    def test_buckets_by_window(self):
        events = [self._ev(-3), self._ev(5), self._ev(20), self._ev(60), self._ev(200)]
        b = litigation_deadline_rules.bucket_deadlines(events, [])
        assert len(b.urgent) == 2  # 逾期 + ≤7日
        assert len(b.due_8_30) == 1
        assert len(b.due_31_90) == 1
        # 200 天外不进任何告警桶
        assert b.has_alerts() is True
        assert b.top_priority() == "high"

    def test_met_overdue_not_urgent(self):
        b = litigation_deadline_rules.bucket_deadlines([self._ev(-3, status="met")], [])
        assert b.urgent == []

    def test_legal_hold_refresh_bucketed(self):
        lh = SimpleNamespace(
            id="lh1",
            matter_id="m1",
            subject="保全A",
            result_json=json.dumps(
                {"next_refresh": (date.today() + timedelta(days=10)).isoformat()}
            ),
        )
        b = litigation_deadline_rules.bucket_deadlines([], [lh])
        assert len(b.due_8_30) == 1 and b.due_8_30[0]["type"] == "legal_hold"

    def test_add_status_changes_and_report(self):
        b = litigation_deadline_rules.DocketBuckets()
        litigation_deadline_rules.add_status_changes(
            b, [SimpleNamespace(id="e1", matter_id="m1", event_type="substantive", summary="判决")]
        )
        assert len(b.status_change) == 1
        report = litigation_deadline_rules.render_docket_report(b)
        assert "态势变化" in report and "线索非日程" in report

    def test_empty_report_says_no_alerts(self):
        report = litigation_deadline_rules.render_docket_report(
            litigation_deadline_rules.DocketBuckets()
        )
        assert "本周无紧急案件事项" in report


# --------------------------------------------------------------------------- #
# Docket-watcher scheduled task
# --------------------------------------------------------------------------- #
class TestDocketWatcher:
    def test_run_writes_notification_for_configured_user(self, db, user_id):
        litigation_profile_repo.create(
            db, user_id=user_id, user_role="lawyer", setup_status="completed"
        )
        m = litigation_matter_repo.create(db, user_id=user_id, case_name="活跃案", status="active")
        litigation_matter_event_repo.create(
            db,
            matter_id=m.id,
            user_id=user_id,
            event_type="deadline",
            event_date=date.today(),
            due_date=date.today() + timedelta(days=3),
            summary="上诉期届满",
        )
        written = litigation_docket_watcher.run(db)
        assert written == 1
        notes, total = litigation_notification_repo.list_by_user(db, user_id=user_id)
        assert total == 1 and notes[0].priority == "high"

    def test_run_skips_unconfigured_user(self, db, user_id):
        # No profile / not completed → skipped.
        assert litigation_docket_watcher.run(db) == 0


# --------------------------------------------------------------------------- #
# C1 regression: law tool must be async + return valid JSON (never crash)
# --------------------------------------------------------------------------- #
class TestLawToolC1Regression:
    def test_research_litigation_rules_is_async(self):
        assert inspect.iscoroutinefunction(research_litigation_rules)

    def test_research_litigation_rules_returns_valid_json(self, db, user_id):
        litigation_profile_repo.create(
            db,
            user_id=user_id,
            user_role="lawyer",
            setup_status="completed",
            dispute_profile=json.dumps({"common_courts": ["北京朝阳法院"]}, ensure_ascii=False),
        )
        ctx = SimpleNamespace(deps=LitigationDeps(user_id=user_id, db=db))
        out = asyncio.run(research_litigation_rules(ctx, "证据保全 民诉法§81"))
        parsed = json.loads(out)
        assert parsed["topic"] == "证据保全 民诉法§81"
        assert parsed["dispute_profile"] == {"common_courts": ["北京朝阳法院"]}
        assert "note" in parsed


# --------------------------------------------------------------------------- #
# Agent factory structural consistency
# --------------------------------------------------------------------------- #
class TestAgentFactory:
    def test_skill_maps_consistent(self):
        skills = set(_PROMPT_BUILDERS)
        assert len(skills) == 11
        assert set(_SKILL_TOOLS) == skills
        # demand skills do NOT record analyses
        assert set(SKILL_ANALYSIS_TYPE) == skills - {"demand_draft", "demand_received"}
        assert len(SKILL_ANALYSIS_TYPE) == 9
        assert skills >= _LAW_TOOL_SKILLS

    def test_create_agent_builds_and_unknown_raises(self):
        agent = create_litigation_agent(
            "claim_chart", provider="openai", model_name="gpt-4o-mini", api_key="test-key"
        )
        assert agent is not None
        with pytest.raises(ValueError):
            create_litigation_agent("not_a_skill")  # type: ignore[arg-type]
