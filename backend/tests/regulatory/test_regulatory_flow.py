"""Data-layer tests for the regulatory-legal module (Phase 1).

Covers the 6 repositories and the deterministic invariants that live at the
repo level, including the plan-eng-review (2026-06-13) decisions:
- A1  feed-check watermark advance (set_last_feed_check).
- A3  gap dedup on (regulation_citation + policy_affected), fallback to
      requirement text only when citation is absent.
- cron dedup via reg_item dedup_key.
- comment reminder cadence (list_due_within).

Agent / WS / cron / service tests follow in later phases (mirrors how
tests/litigation/test_litigation_flow.py grows).
"""

import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.agents.regulatory.agent import SKILL_ANALYSIS_TYPE, create_regulatory_agent
from app.agents.regulatory.deps import RegulatoryDeps
from app.agents.regulatory.prompts import build_reg_feed_watch_system_prompt
from app.agents.regulatory.tools.analysis_tools import save_gap
from app.agents.regulatory.tools.feed_tools import save_reg_item
from app.core.exceptions import ValidationError
from app.repositories import (
    regulatory_comment_repo,
    regulatory_gap_repo,
    regulatory_notification_repo,
    regulatory_profile_repo,
    regulatory_reg_item_repo,
)
from app.schemas.regulatory.cold_start import ColdStartRequest
from app.schemas.regulatory.comment import RegulatoryCommentDecide
from app.schemas.regulatory.gap import (
    RegulatoryGapAccept,
    RegulatoryGapClose,
)
from app.schemas.regulatory.profile import RegulatoryProfileUpdate
from app.services.regulatory_cold_start_service import RegulatoryColdStartService
from app.services.regulatory_comment_service import RegulatoryCommentService
from app.services.regulatory_gap_service import RegulatoryGapService
from app.services.regulatory_profile_service import RegulatoryProfileService
from app.tasks import regulatory_feed_fetcher, regulatory_reg_change_monitor
from app.tasks.regulatory_materiality_rules import (
    classify_materiality,
    render_tier_table_for_prompt,
)


# --------------------------------------------------------------------------- #
# Profile repo + A1 watermark
# --------------------------------------------------------------------------- #
class TestProfileRepo:
    def test_create_then_get_by_user(self, db, user_id):
        created = regulatory_profile_repo.create(
            db, user_id=user_id, practice_setting="法务内部", setup_status="completed"
        )
        assert created.id
        fetched = regulatory_profile_repo.get_by_user_id(db, user_id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.setup_status == "completed"

    def test_set_last_feed_check_advances_watermark(self, db, user_id):
        profile = regulatory_profile_repo.create(db, user_id=user_id)
        assert profile.last_feed_check_at is None
        ts = datetime(2026, 6, 13, 10, 37, tzinfo=UTC)
        updated = regulatory_profile_repo.set_last_feed_check(db, profile=profile, ts=ts)
        # SQLite stores DateTime as naive — compare wall-clock components, not tzinfo.
        assert updated.last_feed_check_at is not None
        assert updated.last_feed_check_at.replace(tzinfo=None) == ts.replace(tzinfo=None)


# --------------------------------------------------------------------------- #
# Reg-item repo + cron dedup_key
# --------------------------------------------------------------------------- #
class TestRegItemRepo:
    def test_find_by_dedup_key_hit_and_miss(self, db, user_id):
        regulatory_reg_item_repo.create(
            db, user_id=user_id, title="某规定", dedup_key="abc123", materiality="always"
        )
        hit = regulatory_reg_item_repo.find_by_dedup_key(db, user_id=user_id, dedup_key="abc123")
        assert hit is not None
        miss = regulatory_reg_item_repo.find_by_dedup_key(db, user_id=user_id, dedup_key="nope")
        assert miss is None

    def test_dedup_key_is_per_user(self, db, user_id):
        regulatory_reg_item_repo.create(db, user_id=user_id, dedup_key="shared")
        # 另一个用户的相同 dedup_key 不应命中本用户查询
        import uuid

        from app.db.models.user import User

        other = str(uuid.uuid4())
        db.add(User(id=other, email=f"{other[:8]}@t.local", hashed_password="x" * 60))
        db.flush()
        assert (
            regulatory_reg_item_repo.find_by_dedup_key(db, user_id=other, dedup_key="shared")
            is None
        )

    def test_list_paginated_filters_by_materiality(self, db, user_id):
        regulatory_reg_item_repo.create(db, user_id=user_id, materiality="always", dedup_key="a")
        regulatory_reg_item_repo.create(db, user_id=user_id, materiality="fyi", dedup_key="b")
        items, total = regulatory_reg_item_repo.list_paginated(
            db, user_id=user_id, materiality="always"
        )
        assert total == 1
        assert items[0].materiality == "always"


# --------------------------------------------------------------------------- #
# Gap repo — A3 dedup
# --------------------------------------------------------------------------- #
class TestGapDedupA3:
    def test_dedup_by_citation_and_policy(self, db, user_id):
        regulatory_gap_repo.create(
            db,
            user_id=user_id,
            requirement="应当在显著位置披露X（措辞甲）",
            regulation_citation="《某法》第十二条",
            policy_affected="隐私政策",
            gap_type="partial",
        )
        # 重跑 policy-diff：requirement 措辞漂移，但法条引用 + 政策相同 → 命中去重
        dup = regulatory_gap_repo.find_duplicate(
            db,
            user_id=user_id,
            regulation_citation="《某法》第十二条",
            policy_affected="隐私政策",
            requirement_normalized="需公开X（措辞乙）",
        )
        assert dup is not None

    def test_different_policy_is_not_duplicate(self, db, user_id):
        regulatory_gap_repo.create(
            db,
            user_id=user_id,
            regulation_citation="《某法》第十二条",
            policy_affected="隐私政策",
        )
        dup = regulatory_gap_repo.find_duplicate(
            db,
            user_id=user_id,
            regulation_citation="《某法》第十二条",
            policy_affected="数据安全政策",
        )
        assert dup is None

    def test_fallback_to_requirement_when_citation_absent(self, db, user_id):
        regulatory_gap_repo.create(
            db,
            user_id=user_id,
            requirement="必须保留日志6个月",
            policy_affected="日志政策",
        )
        # 无法条引用 → 回退到归一化 requirement 文本匹配
        dup = regulatory_gap_repo.find_duplicate(
            db,
            user_id=user_id,
            policy_affected="日志政策",
            requirement_normalized="必须保留日志6个月",
        )
        assert dup is not None

    def test_list_open_excludes_closed_and_risk_accepted(self, db, user_id):
        regulatory_gap_repo.create(db, user_id=user_id, policy_affected="P1", status="open")
        regulatory_gap_repo.create(db, user_id=user_id, policy_affected="P2", status="closed")
        regulatory_gap_repo.create(
            db, user_id=user_id, policy_affected="P3", status="risk-accepted"
        )
        open_gaps = regulatory_gap_repo.list_open(db, user_id=user_id)
        assert {g.policy_affected for g in open_gaps} == {"P1"}


# --------------------------------------------------------------------------- #
# Comment repo — reminder cadence
# --------------------------------------------------------------------------- #
class TestCommentReminders:
    def test_list_due_within_window(self, db, user_id):
        today = date(2026, 6, 13)
        regulatory_comment_repo.create(
            db,
            user_id=user_id,
            regulation="征求意见稿A",
            comment_deadline=today + timedelta(days=10),
            decision="undecided",
        )
        regulatory_comment_repo.create(
            db,
            user_id=user_id,
            regulation="征求意见稿B",
            comment_deadline=today + timedelta(days=40),
            decision="undecided",
        )
        due = regulatory_comment_repo.list_due_within(db, user_id=user_id, days=14, today=today)
        assert [c.regulation for c in due] == ["征求意见稿A"]

    def test_due_within_excludes_decided(self, db, user_id):
        today = date(2026, 6, 13)
        regulatory_comment_repo.create(
            db,
            user_id=user_id,
            regulation="已决定",
            comment_deadline=today + timedelta(days=3),
            decision="filed",
        )
        due = regulatory_comment_repo.list_due_within(db, user_id=user_id, days=14, today=today)
        assert due == []


# --------------------------------------------------------------------------- #
# Notification repo
# --------------------------------------------------------------------------- #
class TestNotificationRepo:
    def test_create_and_mark_read(self, db, user_id):
        n = regulatory_notification_repo.create(
            db, user_id=user_id, notification_type="reg_digest", title="法规动态简报"
        )
        assert n.is_read is False
        regulatory_notification_repo.mark_read(db, notification=n)
        items, total = regulatory_notification_repo.list_paginated(
            db, user_id=user_id, is_read=True
        )
        assert total == 1
        assert items[0].is_read is True


# --------------------------------------------------------------------------- #
# Materiality classifier — C1 authoritative table + A2 no-keyword→review
# --------------------------------------------------------------------------- #
class TestMaterialityClassifier:
    def test_regulation_from_watched_regulator_is_always(self):
        assert (
            classify_materiality(
                item_type="regulation",
                regulator="国家网信办",
                text="某规定",
                watchlist_regulators=["国家网信办", "市场监管总局"],
            )
            == "always"
        )

    def test_regulation_from_unwatched_regulator_downgrades_to_review(self):
        assert (
            classify_materiality(
                item_type="regulation",
                regulator="某地方厅",
                text="某规定",
                watchlist_regulators=["国家网信办"],
            )
            == "review"
        )

    def test_enforcement_industry_hit_is_always(self):
        assert (
            classify_materiality(
                item_type="enforcement",
                regulator="市场监管总局",
                text="对某互联网平台数据违规处罚",
                industry_keywords=["互联网平台", "数据"],
            )
            == "always"
        )

    def test_enforcement_no_keyword_is_fyi(self):
        assert (
            classify_materiality(item_type="enforcement", regulator="某局", text="对某餐饮企业处罚")
            == "fyi"
        )

    def test_nprm_is_review(self):
        assert classify_materiality(item_type="nprm", regulator="x", text="征求意见稿") == "review"

    def test_speech_is_fyi(self):
        assert classify_materiality(item_type="speech", regulator="x", text="领导讲话") == "fyi"

    def test_a2_unknown_type_defaults_to_review_not_fyi(self):
        # A2 安全网：边界/未知 item_type 默认 review，绝不 fyi
        assert classify_materiality(item_type="weird_new_type", regulator="x", text="?") == "review"

    def test_a2_pre_rule_boundary_is_review(self):
        assert (
            classify_materiality(item_type="pre_rule", regulator="x", text="调研通知") == "review"
        )

    def test_c1_table_renders_for_prompt(self):
        rendered = render_tier_table_for_prompt()
        # C1：权威表渲染含三层级且明示"绝不降为 🟢"
        assert "regulation" in rendered
        assert "绝不降为 🟢" in rendered


# --------------------------------------------------------------------------- #
# Cold-start state machine (6 steps; QUICK=(0,1,2,5))
# --------------------------------------------------------------------------- #
class TestColdStart:
    def test_quick_mode_completes_and_materializes(self, db, user_id):
        svc = RegulatoryColdStartService(db)
        res = None
        for stp in (0, 1, 2, 5):  # QUICK_PLAN
            res = svc.submit_step(
                user_id,
                ColdStartRequest(
                    step=stp,
                    quick_mode=True,
                    answers={"user_role": "lawyer", "practice_setting": "法务内部"}
                    if stp == 0
                    else {},
                ),
            )
        assert res is not None and res.completed is True
        profile = regulatory_profile_repo.get_by_user_id(db, user_id)
        assert profile is not None
        assert profile.setup_status == "completed"
        assert profile.setup_depth == "quick"
        assert profile.user_role == "lawyer"

    def test_invalid_step_for_depth_raises(self, db, user_id):
        svc = RegulatoryColdStartService(db)
        with pytest.raises(ValidationError):
            svc.submit_step(user_id, ColdStartRequest(step=3, quick_mode=True))


# --------------------------------------------------------------------------- #
# C2 trust boundary — save_reg_item provenance enforcement
# --------------------------------------------------------------------------- #
class TestSaveRegItemProvenanceC2:
    def test_unfetched_item_is_force_stamped_unverified(self, db, user_id):
        deps = RegulatoryDeps(user_id=user_id, db=db)  # no fetched_provenance
        ctx = SimpleNamespace(deps=deps)
        save_reg_item(
            ctx,
            title="疑似编造的法规",
            regulator="某机构",
            item_type="regulation",
            summary="模型凭记忆产出",
            source_tag="[原始来源]",  # model claims primary source
            dedup_key="never-fetched",
        )
        items = regulatory_reg_item_repo.list_by_user(db, user_id=user_id)
        assert len(items) == 1
        assert items[0].source_tag == "[模型知识—需验证]"
        assert items[0].status_verified is False

    def test_fetched_item_keeps_claimed_source(self, db, user_id):
        deps = RegulatoryDeps(user_id=user_id, db=db, fetched_provenance={"real-key"})
        ctx = SimpleNamespace(deps=deps)
        save_reg_item(
            ctx,
            title="真实抓取的法规",
            regulator="国家网信办",
            item_type="regulation",
            summary="来自 fetch_reg_feeds",
            source_tag="[中国政府网]",
            dedup_key="real-key",
        )
        items = regulatory_reg_item_repo.list_by_user(db, user_id=user_id)
        assert items[0].source_tag == "[中国政府网]"


# --------------------------------------------------------------------------- #
# save_gap handoff — A3 dedup at the tool boundary
# --------------------------------------------------------------------------- #
class TestSaveGapHandoffA3:
    def test_rerun_same_citation_does_not_duplicate(self, db, user_id):
        deps = RegulatoryDeps(user_id=user_id, db=db)
        ctx = SimpleNamespace(deps=deps)
        save_gap(
            ctx,
            "应披露X（措辞甲）",
            "隐私政策",
            regulation_citation="《个保法》第十七条",
            severity="high",
        )
        save_gap(
            ctx,
            "需公开X（措辞乙）",
            "隐私政策",
            regulation_citation="《个保法》第十七条",
            severity="high",
        )
        open_gaps = regulatory_gap_repo.list_open(db, user_id=user_id)
        assert len(open_gaps) == 1


# --------------------------------------------------------------------------- #
# Agent factory
# --------------------------------------------------------------------------- #
class TestAgentFactory:
    def test_each_skill_builds(self):
        for skill in ("reg_feed_watch", "policy_diff", "policy_redraft"):
            agent = create_regulatory_agent(skill, model_name="gpt-4o-mini", provider="openai")
            assert agent is not None

    def test_unknown_skill_raises(self):
        with pytest.raises(ValueError):
            create_regulatory_agent("nonexistent_skill")  # type: ignore[arg-type]

    def test_analysis_type_mapping(self):
        assert SKILL_ANALYSIS_TYPE["policy_diff"] == "policy_diff"
        assert SKILL_ANALYSIS_TYPE["policy_redraft"] == "policy_redraft"
        assert "reg_feed_watch" not in SKILL_ANALYSIS_TYPE

    def test_reg_feed_prompt_injects_c1_table(self):
        prompt = build_reg_feed_watch_system_prompt()
        # C1：reg-feed-watcher 系统提示必须注入权威层级表
        assert "item_type → 重要度层级" in prompt
        assert "绝不降为 🟢" in prompt


# --------------------------------------------------------------------------- #
# Gap status report — §2.4 invariants (unverified never overdue; observations split)
# --------------------------------------------------------------------------- #
class TestGapStatusReport:
    def test_unverified_overdue_goes_to_open_not_overdue(self, db, user_id):
        past = date(2026, 1, 1)
        regulatory_gap_repo.create(
            db,
            user_id=user_id,
            policy_affected="P-unverified",
            gap_type="full",
            due=past,
            status_verified=False,
        )
        report = RegulatoryGapService(db).status_report(user_id, today=date(2026, 6, 13))
        # §2.4：未验证逾期永不进 🔴 overdue，进 🟡 open_gaps
        assert all(g.policy_affected != "P-unverified" for g in report.overdue)
        assert any(g.policy_affected == "P-unverified" for g in report.open_gaps)

    def test_verified_overdue_goes_to_overdue(self, db, user_id):
        past = date(2026, 1, 1)
        regulatory_gap_repo.create(
            db,
            user_id=user_id,
            policy_affected="P-verified",
            gap_type="full",
            due=past,
            status_verified=True,
        )
        report = RegulatoryGapService(db).status_report(user_id, today=date(2026, 6, 13))
        assert any(g.policy_affected == "P-verified" for g in report.overdue)

    def test_watch_and_comment_decision_go_to_observations(self, db, user_id):
        regulatory_gap_repo.create(
            db, user_id=user_id, policy_affected="W", gap_type="watch", due=date(2026, 1, 1)
        )
        regulatory_gap_repo.create(
            db,
            user_id=user_id,
            policy_affected="C",
            gap_type="comment-decision",
            due=date(2026, 1, 1),
        )
        report = RegulatoryGapService(db).status_report(user_id, today=date(2026, 6, 13))
        obs_policies = {g.policy_affected for g in report.observations}
        assert obs_policies == {"W", "C"}
        # 观察事项不混入合规差距（即便逾期）
        assert not report.overdue
        assert not report.open_gaps

    def test_due_soon_within_30_days(self, db, user_id):
        regulatory_gap_repo.create(
            db,
            user_id=user_id,
            policy_affected="soon",
            gap_type="partial",
            due=date(2026, 6, 20),
            status_verified=True,
        )
        report = RegulatoryGapService(db).status_report(user_id, today=date(2026, 6, 13))
        assert any(g.policy_affected == "soon" for g in report.due_soon)

    def test_close_and_accept_leave_open_report(self, db, user_id):
        svc = RegulatoryGapService(db)
        g1 = regulatory_gap_repo.create(db, user_id=user_id, policy_affected="X", gap_type="full")
        g2 = regulatory_gap_repo.create(db, user_id=user_id, policy_affected="Y", gap_type="full")
        svc.close(g1.id, user_id=user_id, data=RegulatoryGapClose(resolution="已整改"))
        svc.accept_risk(
            g2.id,
            user_id=user_id,
            data=RegulatoryGapAccept(accepted_by="法务总监", accepted_rationale="风险可控"),
        )
        report = svc.status_report(user_id, today=date(2026, 6, 13))
        assert not report.open_gaps and not report.overdue
        # risk-accepted 保留不删
        assert regulatory_gap_repo.get_by_id(db, g2.id).status == "risk-accepted"


# --------------------------------------------------------------------------- #
# Comment decide + notification service
# --------------------------------------------------------------------------- #
class TestCommentDecide:
    def test_filed_sets_filed_at(self, db, user_id):
        c = regulatory_comment_repo.create(
            db, user_id=user_id, regulation="征求意见稿X", decision="undecided"
        )
        svc = RegulatoryCommentService(db)
        updated = svc.decide(
            c.id,
            user_id=user_id,
            data=RegulatoryCommentDecide(decision="filed", rationale="已提交"),
        )
        assert updated.decision == "filed"
        assert updated.filed_at is not None


# --------------------------------------------------------------------------- #
# Profile service (customize upsert)
# --------------------------------------------------------------------------- #
class TestProfileService:
    def test_upsert_creates_then_updates(self, db, user_id):
        svc = RegulatoryProfileService(db)
        created = svc.upsert_my_profile(
            user_id, RegulatoryProfileUpdate(practice_setting="中大型律所")
        )
        assert created.practice_setting == "中大型律所"
        updated = svc.upsert_my_profile(
            user_id, RegulatoryProfileUpdate(watchlist=[{"机构": "网信办"}])
        )
        assert updated.watchlist is not None


# --------------------------------------------------------------------------- #
# Feed fetcher (P1 dedup + A1 per-source status + item_type inference)
# --------------------------------------------------------------------------- #
class TestFeedFetcher:
    def test_infer_item_type(self):
        assert regulatory_feed_fetcher.infer_item_type("关于公开征求意见的通知") == "nprm"
        assert regulatory_feed_fetcher.infer_item_type("某某管理办法") == "regulation"
        assert regulatory_feed_fetcher.infer_item_type("对某公司行政处罚决定") == "enforcement"
        assert regulatory_feed_fetcher.infer_item_type("领导讲话") == "speech"

    def test_p1_dedup_fetches_unique_url_once(self):
        calls: list[str] = []

        def fake(source: dict) -> regulatory_feed_fetcher.SourceOutcome:
            calls.append(source["url"])
            return regulatory_feed_fetcher.SourceOutcome(status="empty")

        sources = [
            {"url": "https://gov.cn/feed", "format": "rss", "name": "A"},
            {"url": "https://gov.cn/feed", "format": "rss", "name": "B"},  # same URL (other user)
            {"url": "https://samr.cn/feed", "format": "rss", "name": "C"},
        ]
        outcomes = regulatory_feed_fetcher.fetch_unique_sources(sources, fetch_fn=fake)
        # P1: same URL fetched once
        assert calls.count("https://gov.cn/feed") == 1
        assert set(outcomes.keys()) == {"https://gov.cn/feed", "https://samr.cn/feed"}

    def test_error_in_one_source_isolated(self):
        def fake(source: dict) -> regulatory_feed_fetcher.SourceOutcome:
            if "bad" in source["url"]:
                raise RuntimeError("boom")
            return regulatory_feed_fetcher.SourceOutcome(status="ok", items=[{"x": 1}])

        sources = [
            {"url": "https://bad.cn/feed", "format": "rss"},
            {"url": "https://good.cn/feed", "format": "rss"},
        ]
        outcomes = regulatory_feed_fetcher.fetch_unique_sources(sources, fetch_fn=fake)
        assert outcomes["https://bad.cn/feed"].status == "error"
        assert outcomes["https://good.cn/feed"].status == "ok"


# --------------------------------------------------------------------------- #
# reg-change-monitor cron — A1 / A2 / P1 / nprm→comment / dedup
# --------------------------------------------------------------------------- #
def _completed_profile_with_feed(db, user_id, sources):
    return regulatory_profile_repo.create(
        db,
        user_id=user_id,
        setup_status="completed",
        feed_config=json.dumps(sources, ensure_ascii=False),
        watchlist=json.dumps([{"机构": "国家网信办"}], ensure_ascii=False),
    )


class TestRegChangeMonitorCron:
    def test_all_sources_error_is_not_all_calm(self, db, user_id):
        _completed_profile_with_feed(
            db, user_id, [{"url": "https://x.cn/feed", "format": "rss", "name": "X源"}]
        )

        def fake(source):
            return regulatory_feed_fetcher.SourceOutcome(status="error", error="500")

        written = regulatory_reg_change_monitor.run(db, fetch_fn=fake)
        assert written == 1
        notes, _ = regulatory_notification_repo.list_paginated(db, user_id=user_id)
        content = notes[0].content or ""
        # A1: 全源 error 绝不显示"一切平静"，且列出失败源 + 高优先级
        assert "一切平静" not in content
        assert "X源" in content
        assert notes[0].priority == "high"
        # A1: 有源失败 → 水位线不前移
        profile = regulatory_profile_repo.get_by_user_id(db, user_id)
        assert profile.last_feed_check_at is None

    def test_healthy_empty_is_all_calm_and_advances_watermark(self, db, user_id):
        _completed_profile_with_feed(
            db, user_id, [{"url": "https://x.cn/feed", "format": "rss", "name": "X源"}]
        )

        def fake(source):
            return regulatory_feed_fetcher.SourceOutcome(status="empty")

        regulatory_reg_change_monitor.run(db, fetch_fn=fake)
        notes, _ = regulatory_notification_repo.list_paginated(db, user_id=user_id)
        # "一切平静" 在标题(summary)；正文(markdown)为"监测源全部正常"
        assert "一切平静" in notes[0].title
        assert "全部正常" in (notes[0].content or "")
        # 全源 ok → 水位线前移
        profile = regulatory_profile_repo.get_by_user_id(db, user_id)
        assert profile.last_feed_check_at is not None

    def test_classify_and_digest_lists_always_and_review(self, db, user_id):
        _completed_profile_with_feed(
            db, user_id, [{"url": "https://x.cn/feed", "format": "rss", "name": "网信办"}]
        )

        def fake(source):
            return regulatory_feed_fetcher.SourceOutcome(
                status="ok",
                items=[
                    {
                        "title": "某管理办法",
                        "regulator": "国家网信办",  # on watchlist → regulation+watch → always
                        "summary": "",
                        "item_type": "regulation",
                        "link": "https://x.cn/1",
                        "published_date": None,
                        "comment_deadline": None,
                        "source_tag": "[联网检索—需复核]",
                        "dedup_key": "k1",
                    },
                    {
                        "title": "某监管指引",
                        "regulator": "国家网信办",
                        "summary": "",
                        "item_type": "guidance",  # → review
                        "link": "https://x.cn/2",
                        "published_date": None,
                        "comment_deadline": None,
                        "source_tag": "[联网检索—需复核]",
                        "dedup_key": "k2",
                    },
                ],
            )

        regulatory_reg_change_monitor.run(db, fetch_fn=fake)
        items = regulatory_reg_item_repo.list_by_user(db, user_id=user_id)
        by_mat = {i.title: i.materiality for i in items}
        assert by_mat["某管理办法"] == "always"
        assert by_mat["某监管指引"] == "review"
        notes, _ = regulatory_notification_repo.list_paginated(db, user_id=user_id)
        content = notes[0].content or ""
        # A2: 🔴 与 🟡 都被列举
        assert "某管理办法" in content
        assert "某监管指引" in content

    def test_nprm_creates_comment_period(self, db, user_id):
        _completed_profile_with_feed(
            db, user_id, [{"url": "https://x.cn/feed", "format": "rss", "name": "X"}]
        )

        def fake(source):
            return regulatory_feed_fetcher.SourceOutcome(
                status="ok",
                items=[
                    {
                        "title": "关于公开征求意见的通知",
                        "regulator": "国家网信办",
                        "summary": "",
                        "item_type": "nprm",
                        "link": "https://x.cn/n1",
                        "published_date": None,
                        "comment_deadline": date(2026, 7, 1),
                        "source_tag": "[联网检索—需复核]",
                        "dedup_key": "n1",
                    }
                ],
            )

        regulatory_reg_change_monitor.run(db, fetch_fn=fake)
        comments, total = regulatory_comment_repo.list_paginated(db, user_id=user_id)
        assert total == 1
        assert comments[0].decision == "undecided"
        assert comments[0].comment_deadline == date(2026, 7, 1)

    def test_dedup_skips_on_rerun(self, db, user_id):
        _completed_profile_with_feed(
            db, user_id, [{"url": "https://x.cn/feed", "format": "rss", "name": "X"}]
        )

        def fake(source):
            return regulatory_feed_fetcher.SourceOutcome(
                status="ok",
                items=[
                    {
                        "title": "某办法",
                        "regulator": "国家网信办",
                        "summary": "",
                        "item_type": "regulation",
                        "link": "https://x.cn/1",
                        "published_date": None,
                        "comment_deadline": None,
                        "source_tag": "[联网检索—需复核]",
                        "dedup_key": "same",
                    }
                ],
            )

        regulatory_reg_change_monitor.run(db, fetch_fn=fake)
        regulatory_reg_change_monitor.run(db, fetch_fn=fake)  # re-run
        items = regulatory_reg_item_repo.list_by_user(db, user_id=user_id)
        assert len(items) == 1  # dedup_key skipped the second time
