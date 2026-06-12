"""Litigation-legal module WebSocket endpoint.

`/ws/litigation` — runs one litigation-legal Agent skill per WS message.
Mirrors the ip-legal WS: no cross-run history, fresh Agent per message, same
streaming event names. The skill is chosen explicitly by the client
(`action`) — no LLM intent routing.

Actions (11 total):
    Analysis-producing (pre-create a litigation_analyses row):
        matter_briefing, chronology, claim_chart, subpoena_triage,
        legal_hold, oc_status, brief_section, deposition_prep, privilege_log
    Demand (needs demand_id):
        demand_draft, demand_received

Client → Server:
    {
        "action": "<one of the above>",
        "prompt": "<instruction / pasted text>",   # REQUIRED
        "matter_id": "...",   # optional, for matter-scoped skills
        "demand_id": "...",   # required for demand_draft / demand_received
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

from app.agents.litigation import (
    SKILL_ANALYSIS_TYPE,
    LitigationDeps,
    LitigationSkillName,
    create_litigation_agent,
)
from app.api.deps import get_current_user_ws
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories import (
    litigation_analysis_repo,
    litigation_demand_repo,
    litigation_matter_repo,
    litigation_profile_repo,
)
from app.services.agent import AgentConnectionManager
from app.services.agent_stream import stream_agent_run

logger = logging.getLogger(__name__)

router = APIRouter()
manager = AgentConnectionManager()

# Skills that pre-create an analysis row (9 types, excluding demand skills)
_ANALYSIS_PRECREATE_ACTIONS: frozenset[str] = frozenset(
    {
        "matter_briefing",
        "chronology",
        "claim_chart",
        "subpoena_triage",
        "legal_hold",
        "oc_status",
        "brief_section",
        "deposition_prep",
        "privilege_log",
    }
)
_DEMAND_ACTIONS: frozenset[str] = frozenset({"demand_draft", "demand_received"})

_VALID_ACTIONS: frozenset[str] = _ANALYSIS_PRECREATE_ACTIONS | _DEMAND_ACTIONS


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
                "提供方和 API Key，再使用争议解决技能。"
            ),
            "code": "llm_not_configured",
        },
    )
    return False


async def _run_skill(
    *, websocket: WebSocket, user: User, data: dict[str, Any], action: str
) -> None:
    skill: LitigationSkillName = action  # type: ignore[assignment]
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        await manager.send_event(websocket, "error", {"message": "prompt is required"})
        return
    if not await _require_llm_configured(websocket, user):
        return

    analysis_type: str | None = SKILL_ANALYSIS_TYPE.get(skill)
    demand_id: str | None = None

    # Resolve + ownership-check the demand record before running.
    if action in _DEMAND_ACTIONS:
        demand_id = data.get("demand_id")
        if not demand_id:
            await manager.send_event(websocket, "error", {"message": "demand_id is required"})
            return
        with contextmanager(get_db_session)() as db:
            row = litigation_demand_repo.get_by_id(db, demand_id)
            if row is None or row.user_id != str(user.id):
                await manager.send_event(
                    websocket,
                    "error",
                    {"message": "Demand matter not found or not owned by you"},
                )
                return

    matter_id: str | None = data.get("matter_id")
    # Verify matter ownership if provided
    if matter_id:
        with contextmanager(get_db_session)() as db:
            row = litigation_matter_repo.get_by_id(db, matter_id)
            if row is None or row.user_id != str(user.id):
                await manager.send_event(
                    websocket,
                    "error",
                    {"message": "Matter not found or not owned by you"},
                )
                return

    with contextmanager(get_db_session)() as db:
        profile = litigation_profile_repo.get_by_user_id(db, str(user.id))
        profile_md = profile.profile_content if profile else None

        analysis_id: str | None = None
        if action in _ANALYSIS_PRECREATE_ACTIONS:
            row = litigation_analysis_repo.create(
                db,
                user_id=str(user.id),
                analysis_type=analysis_type or "matter_briefing",
                matter_id=matter_id,
                status="draft",
            )
            analysis_id = row.id
            await manager.send_event(websocket, "analysis_started", {"analysis_id": analysis_id})

        agent = create_litigation_agent(
            skill,
            practice_profile_markdown=profile_md,
            **_resolve_user_llm_config(user),
        )
        deps = LitigationDeps(
            user_id=str(user.id),
            db=db,
            analysis_type=analysis_type,
            analysis_id=analysis_id,
            demand_id=demand_id,
            matter_id=matter_id,
            output_dir=str(Path("outputs") / "litigation" / str(user.id)),
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


@router.websocket("/ws/litigation")
async def litigation_websocket(
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
