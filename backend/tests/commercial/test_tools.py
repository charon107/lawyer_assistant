"""Tests for the commercial-legal agent tools.

We exercise the tool bodies directly with a fake RunContext that
carries our real `CommercialDeps`. PydanticAI itself is not under
test — that's what the agent-factory test is for.
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import pytest

from app.agents.commercial.agent import CommercialDeps
from app.agents.commercial.tools.escalation_tools import (
    read_escalation_matrix,
    write_contract_deviation,
)
from app.agents.commercial.tools.matter_tools import read_matter_context
from app.agents.commercial.tools.playbook_tools import get_playbook
from app.agents.commercial.tools.profile_tools import (
    read_practice_profile,
    write_practice_profile,
)
from app.agents.commercial.tools.review_tools import (
    read_contract_review,
    write_contract_review,
    write_escalation_decision,
    write_stakeholder_summary,
)
from app.repositories import (
    commercial_matter_repo,
    commercial_profile_repo,
    contract_deviation_repo,
    contract_review_repo,
)

# ---------------------------------------------------------------------------
# A tiny stand-in for pydantic_ai.RunContext. The real class takes a model +
# usage tracker etc; tools only ever read `ctx.deps`, so this is enough.
# ---------------------------------------------------------------------------


@dataclass
class _FakeRunContext:
    deps: Any


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# read_practice_profile
# ---------------------------------------------------------------------------


class TestReadPracticeProfile:
    def test_returns_warning_when_no_profile(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(read_practice_profile(_FakeRunContext(deps)))
        assert "尚未完成" in result

    def test_returns_warning_when_setup_not_completed(self, db, user_id):
        commercial_profile_repo.create(db, user_id=user_id, setup_status="in_progress")
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(read_practice_profile(_FakeRunContext(deps)))
        assert "尚未完成" in result

    def test_returns_full_profile_when_completed(self, db, user_id):
        commercial_profile_repo.create(
            db,
            user_id=user_id,
            company_name="Acme",
            side="purchasing",
            gc_name="Jane",
            monthly_volume="20-50",
            profile_content="# 我的实践画像\n标准合同周期 12 个月。",
            setup_status="completed",
        )
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(read_practice_profile(_FakeRunContext(deps)))
        assert "Acme" in result
        assert "purchasing" in result
        assert "Jane" in result
        assert "20-50" in result
        assert "标准合同周期" in result


# ---------------------------------------------------------------------------
# write_practice_profile
# ---------------------------------------------------------------------------


class TestWritePracticeProfile:
    def test_creates_when_absent(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(write_practice_profile(_FakeRunContext(deps), "# Fresh\n"))
        assert result == "ok"
        profile = commercial_profile_repo.get_by_user_id(db, user_id)
        assert profile is not None
        assert profile.profile_content == "# Fresh\n"
        assert profile.setup_status == "in_progress"

    def test_updates_when_present(self, db, user_id):
        commercial_profile_repo.create(
            db, user_id=user_id, profile_content="old", setup_status="completed"
        )
        deps = CommercialDeps(user_id=user_id, db=db)
        _run(write_practice_profile(_FakeRunContext(deps), "new"))
        profile = commercial_profile_repo.get_by_user_id(db, user_id)
        assert profile.profile_content == "new"
        assert profile.setup_status == "completed"  # untouched on update


# ---------------------------------------------------------------------------
# get_playbook
# ---------------------------------------------------------------------------


class TestGetPlaybook:
    def test_no_profile_returns_warning(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(get_playbook(_FakeRunContext(deps), "purchasing"))
        assert "尚未" in result

    def test_no_playbook_for_side(self, db, user_id):
        # Profile exists but neither playbook is set
        commercial_profile_repo.create(db, user_id=user_id)
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(get_playbook(_FakeRunContext(deps), "purchasing"))
        assert "没有配置" in result

    def test_returns_json_for_configured_side(self, db, user_id):
        from app.schemas.commercial.playbook import Playbook, PlaybookEntry

        commercial_profile_repo.create(
            db,
            user_id=user_id,
            playbook_purchasing=Playbook(
                side="purchasing",
                entries=[
                    PlaybookEntry(
                        clause_key="liability_cap",
                        label="责任上限",
                        standard="100%",
                        floor="50%",
                    ),
                ],
            ),
        )
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(get_playbook(_FakeRunContext(deps), "purchasing"))
        decoded = json.loads(result)
        assert decoded["side"] == "purchasing"
        assert decoded["entries"][0]["clause_key"] == "liability_cap"
        assert decoded["entries"][0]["floor"] == "50%"


# ---------------------------------------------------------------------------
# write_contract_review
# ---------------------------------------------------------------------------


class TestWriteContractReview:
    def test_raises_when_review_id_is_none(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db, review_id=None)
        with pytest.raises(RuntimeError, match="review_id is None"):
            _run(
                write_contract_review(
                    _FakeRunContext(deps),
                    result_status="green",
                    result_summary="ok",
                    result_memo="# memo",
                )
            )

    def test_raises_when_review_belongs_to_other_user(self, db, user_id):
        # Setup: a review belonging to a different user.
        from app.db.models.user import User

        other = "00000000-0000-4000-8000-000000000010"
        db.add(User(id=other, email="o@test.local", hashed_password="x" * 60))
        db.flush()
        review = contract_review_repo.create(db, user_id=other, review_type="vendor")

        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        with pytest.raises(PermissionError):
            _run(
                write_contract_review(
                    _FakeRunContext(deps),
                    result_status="green",
                    result_summary="x",
                    result_memo="x",
                )
            )

    def test_persists_full_result(self, db, user_id):
        review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        out = _run(
            write_contract_review(
                _FakeRunContext(deps),
                result_status="yellow",
                result_summary="2 处弱于底线，1 处需要上报。",
                result_memo="# 备忘录\n...",
                deviations=[
                    {
                        "clause_key": "liability_cap",
                        "clause_label": "责任上限",
                        "playbook_position": "100%",
                        "contract_quote": "50%",
                        "why_it_matters": "只能追回一半",
                    }
                ],
                favorable_terms=["争议解决在我方所在地"],
                missing_terms=["数据保护条款"],
                required_approver="GC",
            )
        )
        decoded_out = json.loads(out)
        assert decoded_out["review_id"] == review.id
        assert decoded_out["result_status"] == "yellow"

        # Re-read from DB
        fresh = contract_review_repo.get_by_id(db, review.id)
        assert fresh.result_status == "yellow"
        assert fresh.required_approver == "GC"
        stored = json.loads(fresh.result_json)
        assert stored["deviations"][0]["clause_key"] == "liability_cap"
        assert stored["favorable_terms"] == ["争议解决在我方所在地"]

    def test_coerces_json_string_array_args(self, db, user_id):
        """Some OpenAI-compatible models (Xiaomi MiMo) send array args as
        JSON-encoded strings. The tool must coerce them, not reject them."""
        review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        _run(
            write_contract_review(
                _FakeRunContext(deps),
                result_status="red",
                result_summary="责任上限远低于底线。",
                result_memo="# 备忘录",
                deviations=(
                    '[{"clause_key": "liability_cap", "clause_label": "责任上限", '
                    '"playbook_position": "100%", "contract_quote": "20%", '
                    '"why_it_matters": "远低于底线"}]'
                ),
                favorable_terms="[]",
                missing_terms='["数据保护条款"]',
            )
        )
        fresh = contract_review_repo.get_by_id(db, review.id)
        stored = json.loads(fresh.result_json)
        assert stored["deviations"][0]["clause_key"] == "liability_cap"
        assert stored["favorable_terms"] == []
        assert stored["missing_terms"] == ["数据保护条款"]

    def test_raises_model_retry_on_non_array_string(self, db, user_id):
        from pydantic_ai import ModelRetry

        review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        with pytest.raises(ModelRetry):
            _run(
                write_contract_review(
                    _FakeRunContext(deps),
                    result_status="green",
                    result_summary="x",
                    result_memo="x",
                    missing_terms='{"not": "an array"}',
                )
            )


# ---------------------------------------------------------------------------
# read_matter_context
# ---------------------------------------------------------------------------


class TestReadMatterContext:
    def test_returns_card_for_own_matter(self, db, user_id):
        matter = commercial_matter_repo.create(
            db,
            user_id=user_id,
            matter_name="Acme 采购框架",
            counterparty="Acme Inc.",
            agreement_type="vendor",
            owner="张三",
            notes="对方付款一向拖延。",
        )
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(read_matter_context(_FakeRunContext(deps), matter.id))
        assert "关联事项背景" in result
        assert "Acme 采购框架" in result
        assert "Acme Inc." in result
        assert "张三" in result
        assert "对方付款一向拖延" in result

    def test_returns_prompt_when_matter_missing(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(read_matter_context(_FakeRunContext(deps), "no-such-id"))
        assert "未找到事项" in result

    def test_does_not_leak_other_users_matter(self, db, user_id):
        from app.db.models.user import User

        other = "00000000-0000-4000-8000-000000000020"
        db.add(User(id=other, email="o2@test.local", hashed_password="x" * 60))
        db.flush()
        matter = commercial_matter_repo.create(
            db, user_id=other, matter_name="机密事项", counterparty="Secret Co."
        )
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(read_matter_context(_FakeRunContext(deps), matter.id))
        assert "未找到事项" in result
        assert "Secret Co." not in result


# ---------------------------------------------------------------------------
# read_escalation_matrix
# ---------------------------------------------------------------------------


class TestReadEscalationMatrix:
    def test_warns_when_no_profile(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(read_escalation_matrix(_FakeRunContext(deps)))
        assert "尚未完成实践画像配置" in result

    def test_warns_when_matrix_not_configured(self, db, user_id):
        commercial_profile_repo.create(db, user_id=user_id)
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(read_escalation_matrix(_FakeRunContext(deps)))
        assert "尚未配置上报矩阵" in result

    def test_returns_matrix_verbatim_when_configured(self, db, user_id):
        matrix = json.dumps(
            [{"severity": "red", "approver": "CFO", "channel": "飞书"}],
            ensure_ascii=False,
        )
        profile = commercial_profile_repo.create(db, user_id=user_id)
        profile.escalation_matrix = matrix
        db.flush()
        deps = CommercialDeps(user_id=user_id, db=db)
        result = _run(read_escalation_matrix(_FakeRunContext(deps)))
        assert result == matrix
        assert "CFO" in result


# ---------------------------------------------------------------------------
# write_contract_deviation
# ---------------------------------------------------------------------------


class TestWriteContractDeviation:
    def test_raises_when_review_id_is_none(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db, review_id=None)
        with pytest.raises(RuntimeError, match="review_id is None"):
            _run(
                write_contract_deviation(
                    _FakeRunContext(deps),
                    clause_key="liability_cap",
                )
            )

    def test_raises_when_review_belongs_to_other_user(self, db, user_id):
        from app.db.models.user import User

        other = "00000000-0000-4000-8000-000000000030"
        db.add(User(id=other, email="o3@test.local", hashed_password="x" * 60))
        db.flush()
        review = contract_review_repo.create(db, user_id=other, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        with pytest.raises(PermissionError):
            _run(
                write_contract_deviation(
                    _FakeRunContext(deps),
                    clause_key="liability_cap",
                )
            )

    def test_persists_deviation(self, db, user_id):
        review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        out = _run(
            write_contract_deviation(
                _FakeRunContext(deps),
                clause_key="liability_cap",
                clause_label="责任上限",
                playbook_position="100%",
                signed_position="50%",
                severity_legal="orange",
                severity_commercial="yellow",
                category="liability",
            )
        )
        deviation_id = json.loads(out)["deviation_id"]
        stored = contract_deviation_repo.get_by_id(db, deviation_id)
        assert stored is not None
        assert stored.review_id == review.id
        assert stored.user_id == user_id
        assert stored.clause_key == "liability_cap"
        assert stored.severity_legal == "orange"
        assert stored.severity_commercial == "yellow"


# ---------------------------------------------------------------------------
# read_contract_review
# ---------------------------------------------------------------------------


class TestReadContractReview:
    def test_raises_when_review_id_is_none(self, db, user_id):
        deps = CommercialDeps(user_id=user_id, db=db, review_id=None)
        with pytest.raises(RuntimeError, match="review_id is None"):
            _run(read_contract_review(_FakeRunContext(deps)))

    def test_raises_when_review_belongs_to_other_user(self, db, user_id):
        from app.db.models.user import User

        other = "00000000-0000-4000-8000-000000000040"
        db.add(User(id=other, email="o4@test.local", hashed_password="x" * 60))
        db.flush()
        review = contract_review_repo.create(db, user_id=other, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        with pytest.raises(PermissionError):
            _run(read_contract_review(_FakeRunContext(deps)))

    def test_returns_review_fields(self, db, user_id):
        review = contract_review_repo.create(
            db,
            user_id=user_id,
            review_type="saas",
            counterparty="Cloud Co.",
            agreement_name="主服务协议",
        )
        contract_review_repo.update_result(
            db,
            review=review,
            result_status="yellow",
            result_summary="两处弱于底线。",
            result_memo="# 备忘录",
        )
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        decoded = json.loads(_run(read_contract_review(_FakeRunContext(deps))))
        assert decoded["review_id"] == review.id
        assert decoded["review_type"] == "saas"
        assert decoded["counterparty"] == "Cloud Co."
        assert decoded["agreement_name"] == "主服务协议"
        assert decoded["result_status"] == "yellow"
        assert decoded["result_summary"] == "两处弱于底线。"


# ---------------------------------------------------------------------------
# write_stakeholder_summary
# ---------------------------------------------------------------------------


class TestWriteStakeholderSummary:
    def test_persists_summary(self, db, user_id):
        review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        out = _run(
            write_stakeholder_summary(
                _FakeRunContext(deps),
                "🟡 可以签，但责任上限只覆盖合同额一半。",
            )
        )
        assert json.loads(out)["review_id"] == review.id
        fresh = contract_review_repo.get_by_id(db, review.id)
        assert "可以签" in fresh.stakeholder_summary

    def test_raises_when_review_belongs_to_other_user(self, db, user_id):
        from app.db.models.user import User

        other = "00000000-0000-4000-8000-000000000050"
        db.add(User(id=other, email="o5@test.local", hashed_password="x" * 60))
        db.flush()
        review = contract_review_repo.create(db, user_id=other, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        with pytest.raises(PermissionError):
            _run(write_stakeholder_summary(_FakeRunContext(deps), "x"))


# ---------------------------------------------------------------------------
# write_escalation_decision
# ---------------------------------------------------------------------------


class TestWriteEscalationDecision:
    def test_persists_decision_defaults_not_sent(self, db, user_id):
        review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        out = _run(
            write_escalation_decision(
                _FakeRunContext(deps),
                required_approver="CFO",
            )
        )
        decoded = json.loads(out)
        assert decoded["review_id"] == review.id
        assert decoded["required_approver"] == "CFO"
        fresh = contract_review_repo.get_by_id(db, review.id)
        assert fresh.required_approver == "CFO"
        assert fresh.escalation_sent is False

    def test_records_sent_flag_when_true(self, db, user_id):
        review = contract_review_repo.create(db, user_id=user_id, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        _run(
            write_escalation_decision(
                _FakeRunContext(deps),
                required_approver="GC",
                escalation_sent=True,
            )
        )
        fresh = contract_review_repo.get_by_id(db, review.id)
        assert fresh.escalation_sent is True

    def test_raises_when_review_belongs_to_other_user(self, db, user_id):
        from app.db.models.user import User

        other = "00000000-0000-4000-8000-000000000060"
        db.add(User(id=other, email="o6@test.local", hashed_password="x" * 60))
        db.flush()
        review = contract_review_repo.create(db, user_id=other, review_type="vendor")
        deps = CommercialDeps(user_id=user_id, db=db, review_id=review.id)
        with pytest.raises(PermissionError):
            _run(write_escalation_decision(_FakeRunContext(deps), required_approver="GC"))
