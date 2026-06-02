"""Deterministic depth guard on write_contract_review.

The system prompt (§5/§6) asks the model not to greenlight a defaults-only
config, but model compliance is not guaranteed. This guard is the
non-LLM backstop: a "green" result is forced to "yellow" whenever the
user's config is quick/defaults or the matching-side playbook is missing.
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from app.agents.commercial.agent import CommercialDeps
from app.agents.commercial.tools.review_tools import write_contract_review
from app.repositories import commercial_profile_repo, contract_review_repo


@dataclass
class _FakeRunContext:
    deps: Any


def _run(coro):
    return asyncio.run(coro)


def _write_green(db, user_id, review_id):
    return _run(
        write_contract_review(
            _FakeRunContext(CommercialDeps(user_id=user_id, db=db, review_id=review_id)),
            result_status="green",
            result_summary="完全落在标准范围内，可直接签。",
            result_memo="# 备忘录\n全绿。",
        )
    )


def test_quick_depth_downgrades_green_to_yellow(db, user_id):
    commercial_profile_repo.create(
        db, user_id=user_id, setup_depth="quick", setup_status="completed"
    )
    review = contract_review_repo.create(db, user_id=user_id, review_type="nda", side="purchasing")
    out = json.loads(_write_green(db, user_id, review.id))
    assert out["result_status"] == "yellow"

    fresh = contract_review_repo.get_by_id(db, review.id)
    assert fresh.result_status == "yellow"
    assert "降级" in (fresh.result_summary or "") or "降级" in (fresh.result_memo or "")


def test_missing_matching_playbook_downgrades_green(db, user_id):
    # Full depth but no purchasing playbook configured.
    commercial_profile_repo.create(
        db, user_id=user_id, setup_depth="full", setup_status="completed"
    )
    review = contract_review_repo.create(
        db, user_id=user_id, review_type="vendor", side="purchasing"
    )
    out = json.loads(_write_green(db, user_id, review.id))
    assert out["result_status"] == "yellow"


def test_full_depth_with_matching_playbook_keeps_green(db, user_id):
    commercial_profile_repo.create(
        db,
        user_id=user_id,
        setup_depth="full",
        playbook_purchasing={"side": "purchasing", "entries": []},
        setup_status="completed",
    )
    review = contract_review_repo.create(
        db, user_id=user_id, review_type="vendor", side="purchasing"
    )
    out = json.loads(_write_green(db, user_id, review.id))
    assert out["result_status"] == "green"

    fresh = contract_review_repo.get_by_id(db, review.id)
    assert fresh.result_status == "green"
