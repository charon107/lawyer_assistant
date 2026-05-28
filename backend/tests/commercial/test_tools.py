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
from app.agents.commercial.tools.playbook_tools import get_playbook
from app.agents.commercial.tools.profile_tools import (
    read_practice_profile,
    write_practice_profile,
)
from app.agents.commercial.tools.review_tools import write_contract_review
from app.repositories import (
    commercial_profile_repo,
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
