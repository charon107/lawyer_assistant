"""Employment-legal module WebSocket endpoint.

`/ws/employment` — runs one employment-legal Agent skill per WS message.
Mirrors the corporate-legal WS: no cross-run history, fresh Agent per
message, same streaming event names. The skill is chosen explicitly by the
client (`action`) — no LLM intent routing.

Actions:
    Review (user-scoped):   hiring, termination, classification, policy, wage_hour, handbook
    Expansion (needs expansion_id): expansion_analyze
    Investigation (needs investigation_id): inv_add, inv_query, inv_memo, inv_summary

Client → Server:
    {
        "action": "<one of the above>",
        "prompt": "<instruction / pasted text>",        # REQUIRED
        "investigation_id": "...",   # required for inv_* actions
        "expansion_id": "...",       # required for expansion_analyze
    }

Server → Client event types: text_delta / tool_call / tool_result /
final_result / complete / error.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.agents.employment import EmploymentDeps, EmploymentSkillName, create_employment_agent
from app.api.deps import get_current_user_ws
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories import (
    employment_expansion_repo,
    employment_investigation_repo,
    employment_profile_repo,
)
from app.services.agent import AgentConnectionManager
from app.services.agent_stream import stream_agent_run

logger = logging.getLogger(__name__)

router = APIRouter()
manager = AgentConnectionManager()

_REVIEW_ACTIONS: dict[str, str] = {
    "hiring": "hiring",
    "termination": "termination",
    "classification": "worker_classification",
    "policy": "policy",
    "wage_hour": "wage_hour",
    "handbook": "handbook",
}
_INVESTIGATION_ACTIONS: frozenset[str] = frozenset(
    {"inv_add", "inv_query", "inv_memo", "inv_summary"}
)
_EXPANSION_ACTIONS: frozenset[str] = frozenset({"expansion_analyze"})

_VALID_ACTIONS: frozenset[str] = (
    frozenset(_REVIEW_ACTIONS) | _INVESTIGATION_ACTIONS | _EXPANSION_ACTIONS
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
                "提供方和 API Key，再使用劳动用工技能。"
            ),
            "code": "llm_not_configured",
        },
    )
    return False


async def _run_skill(
    *, websocket: WebSocket, user: User, data: dict[str, Any], action: str
) -> None:
    skill: EmploymentSkillName = action  # type: ignore[assignment]
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        await manager.send_event(websocket, "error", {"message": "prompt is required"})
        return
    if not await _require_llm_configured(websocket, user):
        return

    review_type: str | None = _REVIEW_ACTIONS.get(action)
    investigation_id: str | None = None
    expansion_id: str | None = None

    # Resolve + ownership-check the scoped parent for investigation / expansion.
    if action in _INVESTIGATION_ACTIONS:
        investigation_id = data.get("investigation_id")
        if not investigation_id:
            await manager.send_event(
                websocket, "error", {"message": "investigation_id is required"}
            )
            return
        with contextmanager(get_db_session)() as db:
            inv = employment_investigation_repo.get_by_id(db, investigation_id)
            if inv is None or inv.user_id != str(user.id):
                await manager.send_event(
                    websocket, "error", {"message": "Investigation not found or not owned by you"}
                )
                return
    elif action in _EXPANSION_ACTIONS:
        expansion_id = data.get("expansion_id")
        if not expansion_id:
            await manager.send_event(websocket, "error", {"message": "expansion_id is required"})
            return
        with contextmanager(get_db_session)() as db:
            exp = employment_expansion_repo.get_by_id(db, expansion_id)
            if exp is None or exp.user_id != str(user.id):
                await manager.send_event(
                    websocket, "error", {"message": "Expansion not found or not owned by you"}
                )
                return

    with contextmanager(get_db_session)() as db:
        profile = employment_profile_repo.get_by_user_id(db, str(user.id))
        profile_md = profile.profile_content if profile else None

        agent = create_employment_agent(
            skill,
            practice_profile_markdown=profile_md,
            **_resolve_user_llm_config(user),
        )
        deps = EmploymentDeps(
            user_id=str(user.id),
            db=db,
            review_type=review_type,
            investigation_id=investigation_id,
            expansion_id=expansion_id,
            output_dir=str(Path("outputs") / "employment" / str(user.id)),
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


@router.websocket("/ws/employment")
async def employment_websocket(
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
