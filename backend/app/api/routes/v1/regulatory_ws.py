"""Regulatory-legal module WebSocket endpoint.

`/ws/regulatory` — runs one regulatory-legal Agent skill per WS message.
Mirrors the ip / litigation WS: no cross-run history, fresh Agent per message,
same streaming event names. The skill is chosen explicitly by the client
(`action`) — no LLM intent routing.

Actions (3 total):
    Analysis-producing (pre-create a regulatory_analyses row):
        policy_diff, policy_redraft
    Feed (no pre-created row; writes reg_items / comments via tools):
        reg_feed_watch

Client → Server:
    {
        "action": "<one of the above>",
        "prompt": "<instruction / pasted text>",   # REQUIRED
        "reg_item_id": "...",   # optional, for policy_diff against a tracked item
    }

Server → Client event types: analysis_started / text_delta / tool_call /
tool_result / final_result / complete / error.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.agents.regulatory import (
    SKILL_ANALYSIS_TYPE,
    RegulatoryDeps,
    RegulatorySkillName,
    create_regulatory_agent,
)
from app.api.deps import get_current_user_ws
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories import (
    regulatory_analysis_repo,
    regulatory_profile_repo,
    regulatory_reg_item_repo,
)
from app.services.agent import AgentConnectionManager
from app.services.agent_stream import stream_agent_run

logger = logging.getLogger(__name__)

router = APIRouter()
manager = AgentConnectionManager()

_ANALYSIS_PRECREATE_ACTIONS: frozenset[str] = frozenset({"policy_diff", "policy_redraft"})
_FEED_ACTIONS: frozenset[str] = frozenset({"reg_feed_watch"})
_VALID_ACTIONS: frozenset[str] = _ANALYSIS_PRECREATE_ACTIONS | _FEED_ACTIONS


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
                "提供方和 API Key，再使用监管合规技能。"
            ),
            "code": "llm_not_configured",
        },
    )
    return False


async def _run_skill(
    *, websocket: WebSocket, user: User, data: dict[str, Any], action: str
) -> None:
    skill: RegulatorySkillName = action  # type: ignore[assignment]
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        await manager.send_event(websocket, "error", {"message": "prompt is required"})
        return
    if not await _require_llm_configured(websocket, user):
        return

    analysis_type: str | None = SKILL_ANALYSIS_TYPE.get(skill)
    reg_item_id: str | None = data.get("reg_item_id")

    # Verify reg-item ownership if provided.
    if reg_item_id:
        with contextmanager(get_db_session)() as db:
            row = regulatory_reg_item_repo.get_by_id(db, reg_item_id)
            if row is None or row.user_id != str(user.id):
                await manager.send_event(
                    websocket,
                    "error",
                    {"message": "Reg item not found or not owned by you"},
                )
                return

    with contextmanager(get_db_session)() as db:
        profile = regulatory_profile_repo.get_by_user_id(db, str(user.id))
        profile_md = profile.profile_content if profile else None

        analysis_id: str | None = None
        if action in _ANALYSIS_PRECREATE_ACTIONS:
            row = regulatory_analysis_repo.create(
                db,
                user_id=str(user.id),
                analysis_type=analysis_type or "policy_diff",
                reg_item_id=reg_item_id,
                status="draft",
            )
            analysis_id = row.id
            await manager.send_event(websocket, "analysis_started", {"analysis_id": analysis_id})

        agent = create_regulatory_agent(
            skill,
            practice_profile_markdown=profile_md,
            **_resolve_user_llm_config(user),
        )
        deps = RegulatoryDeps(
            user_id=str(user.id),
            db=db,
            analysis_type=analysis_type,
            analysis_id=analysis_id,
            reg_item_id=reg_item_id,
            output_dir=str(Path("outputs") / "regulatory" / str(user.id)),
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


@router.websocket("/ws/regulatory")
async def regulatory_websocket(
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
            if action in _VALID_ACTIONS:
                await _run_skill(websocket=websocket, user=user, data=data, action=action)
            else:
                await manager.send_event(
                    websocket,
                    "error",
                    {
                        "message": (
                            f"Unknown action {action!r}; expected one of {sorted(_VALID_ACTIONS)}."
                        )
                    },
                )
    finally:
        manager.disconnect(websocket)
