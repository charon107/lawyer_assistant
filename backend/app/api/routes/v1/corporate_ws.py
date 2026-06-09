"""Corporate-legal module WebSocket endpoint.

`/ws/corporate` — runs one corporate-legal Agent skill per WS message.
Mirrors the commercial-legal WS: no cross-run history, fresh Agent per
message, same streaming event names. The skill is chosen explicitly by
the client (`action`) — no LLM intent routing.

Actions (all require an active `deal_id` the user owns):
    diligence   diligence-issue-extraction over a deal's data room.
    tabular     tabular-review; pre-creates a TabularReview row the agent
                fills + exports to Excel.
    material    material-contract-schedule from diligence findings.
    summary     deal-team-summary (read-only briefing).

Client → Server:
    {
        "action": "diligence" | "tabular" | "material" | "summary",
        "deal_id": "<deal id>",          # REQUIRED
        "prompt":  "<instruction / pasted text>",  # REQUIRED
        "title":   "...",                # tabular only (defaults to a date)
    }

Server → Client event types:
    deal_resolved   { deal_id }
    tabular_started { tabular_review_id }   (tabular only)
    text_delta      { content }
    tool_call       { tool_call_id, tool_name, args }
    tool_result     { tool_call_id, content }
    final_result    { output }
    complete        {}
    error           { message, code? }
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.agents.corporate import CorporateDeps, SkillName, create_corporate_agent
from app.api.deps import get_current_user_ws
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories import corporate_deal_repo, corporate_profile_repo, tabular_review_repo
from app.services.agent import AgentConnectionManager
from app.services.agent_stream import stream_agent_run

logger = logging.getLogger(__name__)

router = APIRouter()
manager = AgentConnectionManager()

_SKILL_BY_ACTION: dict[str, SkillName] = {
    "diligence": "diligence-issue-extraction",
    "tabular": "tabular-review",
    "material": "material-contract-schedule",
    "summary": "deal-team-summary",
    "board": "board-minutes",
    "consent": "written-consent",
    "integration": "integration-management",
}

# Skills scoped to a deal (need a `deal_id`). board-minutes / written-consent
# are user-scoped governance drafting and do not require a deal.
_DEAL_SCOPED_ACTIONS: frozenset[str] = frozenset(
    {"diligence", "tabular", "material", "summary", "integration"}
)


def _resolve_user_llm_config(user: User) -> dict[str, Any]:
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
    if user.llm_configs:
        return True
    await manager.send_event(
        websocket,
        "error",
        {
            "message": (
                "尚未配置 AI 模型。请先到「个人中心 → 模型配置」添加你的模型"
                "提供方和 API Key，再使用公司并购技能。"
            ),
            "code": "llm_not_configured",
        },
    )
    return False


async def _run_skill(
    *, websocket: WebSocket, user: User, data: dict[str, Any], action: str
) -> None:
    skill = _SKILL_BY_ACTION[action]
    deal_scoped = action in _DEAL_SCOPED_ACTIONS

    deal_id = data.get("deal_id")
    prompt = (data.get("prompt") or "").strip()
    if deal_scoped and not deal_id:
        await manager.send_event(websocket, "error", {"message": "deal_id is required"})
        return
    if not prompt:
        await manager.send_event(websocket, "error", {"message": "prompt is required"})
        return
    if not await _require_llm_configured(websocket, user):
        return

    # Ownership pre-check (fail fast with a clear message).
    if deal_scoped:
        with contextmanager(get_db_session)() as db:
            deal = corporate_deal_repo.get_by_id(db, deal_id)
            if deal is None or deal.user_id != str(user.id):
                await manager.send_event(
                    websocket, "error", {"message": "Deal not found or not owned by you"}
                )
                return
        await manager.send_event(websocket, "deal_resolved", {"deal_id": deal_id})
    else:
        deal_id = None

    # tabular: pre-create the row the agent will fill.
    tabular_review_id: str | None = None
    if skill == "tabular-review":
        with contextmanager(get_db_session)() as db:
            review = tabular_review_repo.create(
                db, deal_id=deal_id, title=data.get("title") or "表格审查"
            )
            tabular_review_id = review.id
            db.commit()
        await manager.send_event(
            websocket, "tabular_started", {"tabular_review_id": tabular_review_id}
        )

    with contextmanager(get_db_session)() as db:
        profile = corporate_profile_repo.get_by_user_id(db, str(user.id))
        profile_md = profile.profile_content if profile else None

        agent = create_corporate_agent(
            skill,
            practice_profile_markdown=profile_md,
            **_resolve_user_llm_config(user),
        )
        deps = CorporateDeps(
            user_id=str(user.id),
            db=db,
            deal_id=deal_id,
            tabular_review_id=tabular_review_id,
            output_dir=str(Path("outputs") / "corporate" / str(user.id)),
        )
        ok = await stream_agent_run(
            manager=manager,
            websocket=websocket,
            agent=agent,
            prompt=prompt,
            deps=deps,
        )
        if not ok:
            return
        db.commit()

    await manager.send_event(websocket, "complete", {})


@router.websocket("/ws/corporate")
async def corporate_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user_ws),
) -> None:
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
            if action in _SKILL_BY_ACTION:
                await _run_skill(websocket=websocket, user=user, data=data, action=action)
            else:
                await manager.send_event(
                    websocket,
                    "error",
                    {
                        "message": (
                            f"Unknown action {action!r}; expected one of "
                            f"{sorted(_SKILL_BY_ACTION)}."
                        )
                    },
                )
    finally:
        manager.disconnect(websocket)
