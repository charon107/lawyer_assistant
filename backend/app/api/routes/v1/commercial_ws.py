"""Commercial-legal module WebSocket endpoint.

`/ws/commercial` — runs one commercial-legal skill per WS message.
Simpler than the general agent WS:

- No conversation history across runs; each WS message starts a fresh
  Agent (and, for `start`, a fresh ContractReview row).
- Tool-call streaming uses the same event names as the general agent
  WS so the frontend chat hook can be cloned with minimal changes.
- The contract type is chosen explicitly by the frontend (`review_type`)
  — we do NOT do LLM intent routing.

Three actions:
    start       Run a contract review (vendor / nda / saas). Pre-creates a
                ContractReview row, then the agent fills it in via its
                `write_contract_review` tool.
    summarize   Run stakeholder-summary over an EXISTING finished review
                (client passes `review_id`); agent writes back the summary.
    escalate    Run escalation-flagger over an EXISTING review; agent writes
                back `required_approver` / `escalation_sent`.

Client → Server message:
    {
        "action": "start" | "summarize" | "escalate",
        # start:
        "review_type": "vendor" | "nda" | "saas",   # default "vendor"
        "side": "purchasing" | "sales",              # falls back to profile.side
        "counterparty": "...",                       # optional
        "agreement_name": "...",                     # optional
        "annual_value": 100000.0,                    # optional
        "contract_text": "<full contract markdown>", # REQUIRED for start
        # summarize / escalate:
        "review_id": "<existing review id>"          # REQUIRED for these
    }

Server → Client event types:
    review_started        { review_id }   (start only)
    text_delta            { content }
    tool_call             { tool_call_id, tool_name, args }
    tool_result           { tool_call_id, content }
    final_result          { output, review_id }
    complete              {}
    error                 { message, code? }
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.agents.commercial import (
    CommercialDeps,
    SkillName,
    create_commercial_agent,
)
from app.api.deps import get_current_user_ws
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories import commercial_profile_repo, contract_review_repo
from app.schemas.commercial.review import ContractReviewCreate
from app.services.agent import AgentConnectionManager
from app.services.agent_stream import stream_agent_run
from app.services.contract_review_service import ContractReviewService

logger = logging.getLogger(__name__)

router = APIRouter()
manager = AgentConnectionManager()


# review_type (client-supplied, explicit) → agent SkillName for the
# `start` action. We do NOT do LLM intent routing — the frontend selector
# is the source of truth for the contract type.
_SKILL_BY_REVIEW_TYPE: dict[str, SkillName] = {
    "vendor": "vendor-agreement-review",
    "nda": "nda-review",
    "saas": "saas-msa-review",
}

# downstream `action` (operates on an existing finished review) → SkillName.
_SKILL_BY_ACTION: dict[str, SkillName] = {
    "summarize": "stakeholder-summary",
    "escalate": "escalation-flagger",
}


def _resolve_user_llm_config(user: User) -> dict[str, Any]:
    """Pick the per-user LLM config to use, falling back to settings.

    Mirrors the resolution in agent.py so commercial WS behaves the
    same way for users who have configured their own provider.
    """
    if not user.llm_configs:
        return {}
    cfg = user.llm_configs[0]
    return {
        "provider": cfg.provider,
        "model_name": cfg.model,
        "api_key": cfg.api_key,
        "base_url": cfg.base_url,
    }


async def _require_llm_configured(websocket: WebSocket, user: User) -> bool:
    """Send the `llm_not_configured` error and return False if no provider.

    We do NOT silently fall back to a shared/default key — the user must
    bring their own model so they control cost, provider and data.
    """
    if user.llm_configs:
        return True
    await manager.send_event(
        websocket,
        "error",
        {
            "message": (
                "尚未配置 AI 模型。请先到「个人中心 → 模型配置」"
                "添加你的模型提供方和 API Key，再开始合同审查。"
            ),
            "code": "llm_not_configured",
        },
    )
    return False


async def _run_one_review(
    *,
    websocket: WebSocket,
    user: User,
    data: dict[str, Any],
) -> None:
    """Drive one contract review (start action) from start to finish."""

    contract_text = data.get("contract_text") or ""
    if not contract_text.strip():
        await manager.send_event(
            websocket,
            "error",
            {"message": "contract_text is required and must be non-empty"},
        )
        return

    review_type = data.get("review_type", "vendor")
    skill = _SKILL_BY_REVIEW_TYPE.get(review_type)
    if skill is None:
        await manager.send_event(
            websocket,
            "error",
            {
                "message": (
                    f"Unknown review_type {review_type!r}; "
                    f"expected one of {sorted(_SKILL_BY_REVIEW_TYPE)}."
                )
            },
        )
        return

    if not await _require_llm_configured(websocket, user):
        return

    with contextmanager(get_db_session)() as db:
        # 1. Pre-create the review row. This gives the agent a stable
        #    row id to write back to via `write_contract_review`.
        profile = commercial_profile_repo.get_by_user_id(db, str(user.id))
        side = data.get("side") or (profile.side if profile else "purchasing")

        create_payload = ContractReviewCreate(
            review_type=data.get("review_type", "vendor"),
            counterparty=data.get("counterparty"),
            agreement_name=data.get("agreement_name"),
            agreement_type=data.get("agreement_type"),
            side=side,
            annual_value=data.get("annual_value"),
            file_path=data.get("file_path"),
            file_name=data.get("file_name"),
            matter_id=data.get("matter_id"),
        )
        review_svc = ContractReviewService(db)
        review = review_svc.start_review(str(user.id), create_payload)
        review_id = review.id
        db.commit()  # commit the in_progress row so other connections see it

    await manager.send_event(websocket, "review_started", {"review_id": review_id})

    # 2. Open a fresh session that the agent's tools will share. The
    #    agent's `write_contract_review` tool will refuse if it sees
    #    a review owned by a different user; we trust review_id is
    #    the one we just created here.
    with contextmanager(get_db_session)() as db:
        profile = commercial_profile_repo.get_by_user_id(db, str(user.id))
        profile_md = profile.profile_content if profile else None

        agent = create_commercial_agent(
            skill,
            practice_profile_markdown=profile_md,
            **_resolve_user_llm_config(user),
        )

        deps = CommercialDeps(
            user_id=str(user.id),
            db=db,
            review_id=review_id,
        )

        # 3. Stream the agent.
        ok = await stream_agent_run(
            manager=manager,
            websocket=websocket,
            agent=agent,
            prompt=contract_text,
            deps=deps,
            review_id=review_id,
        )
        if not ok:
            return
        db.commit()  # persist any tool-side writes

    await manager.send_event(websocket, "complete", {})


async def _run_downstream_skill(
    *,
    websocket: WebSocket,
    user: User,
    data: dict[str, Any],
    action: str,
) -> None:
    """Run stakeholder-summary / escalation-flagger on an EXISTING review.

    Unlike `start`, these actions do not pre-create a review row. The
    client passes the `review_id` of a finished review; the agent reads it
    via `read_contract_review` and writes back via the skill's write tool.
    Ownership is checked here before the agent runs.
    """
    skill = _SKILL_BY_ACTION.get(action)
    if skill is None:  # defensive — caller already validated
        await manager.send_event(websocket, "error", {"message": f"Unknown action {action!r}."})
        return

    review_id = data.get("review_id")
    if not review_id:
        await manager.send_event(
            websocket,
            "error",
            {"message": "review_id is required for this action"},
        )
        return

    if not await _require_llm_configured(websocket, user):
        return

    with contextmanager(get_db_session)() as db:
        # Pre-check ownership so we fail fast with a clear message rather
        # than surfacing the agent tool's PermissionError mid-stream.
        review = contract_review_repo.get_by_id(db, review_id)
        if review is None or review.user_id != str(user.id):
            await manager.send_event(
                websocket,
                "error",
                {"message": "Review not found or not owned by you"},
            )
            return

        profile = commercial_profile_repo.get_by_user_id(db, str(user.id))
        profile_md = profile.profile_content if profile else None

        agent = create_commercial_agent(
            skill,
            practice_profile_markdown=profile_md,
            **_resolve_user_llm_config(user),
        )
        deps = CommercialDeps(
            user_id=str(user.id),
            db=db,
            review_id=review_id,
        )

        prompt = "请基于已完成的合同审查结论执行本技能，读取该审查并写回结果。"

        ok = await stream_agent_run(
            manager=manager,
            websocket=websocket,
            agent=agent,
            prompt=prompt,
            deps=deps,
            review_id=review_id,
        )
        if not ok:
            return
        db.commit()

    await manager.send_event(websocket, "complete", {})


@router.websocket("/ws/commercial")
async def commercial_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user_ws),
) -> None:
    """One WS connection = one or more sequential vendor-reviews.

    Loop:
        receive_json → run review → send `complete` → wait for next.
    """
    if user is None:
        return

    await manager.connect(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except WebSocketDisconnect:
                break

            action = (data or {}).get("action")
            if action == "start":
                await _run_one_review(websocket=websocket, user=user, data=data)
            elif action in _SKILL_BY_ACTION:
                await _run_downstream_skill(
                    websocket=websocket, user=user, data=data, action=action
                )
            else:
                await manager.send_event(
                    websocket,
                    "error",
                    {
                        "message": (
                            f"Unknown action {action!r}; "
                            "expected 'start', 'summarize' or 'escalate'."
                        )
                    },
                )
    finally:
        manager.disconnect(websocket)
