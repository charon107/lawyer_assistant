"""Privacy-legal module WebSocket endpoint.

`/ws/privacy` — runs one privacy-legal Agent skill per WS message. Mirrors
the employment-legal WS: no cross-run history, fresh Agent per message, same
streaming event names. The skill is chosen explicitly by the client
(`action`) — no LLM intent routing.

Actions:
    Review-producing (pre-create a privacy_reviews row):
        triage, dpa, pia, gap
    DSAR (needs dsar_id):
        dsar
    Policy-monitor (tools manage their own rows):
        policy_sweep, policy_query

Client → Server:
    {
        "action": "<one of the above>",
        "prompt": "<instruction / pasted text>",   # REQUIRED
        "subject": "<activity / counterparty / regulation>",  # optional, for review actions
        "dsar_id": "...",   # required for dsar
    }

Server → Client event types: review_started / text_delta / tool_call /
tool_result / final_result / complete / error.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.agents.privacy import (
    SKILL_REVIEW_TYPE,
    PrivacyDeps,
    PrivacySkillName,
    create_privacy_agent,
)
from app.api.deps import get_current_user_ws
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories import privacy_dsar_repo, privacy_profile_repo, privacy_review_repo
from app.services.agent import AgentConnectionManager
from app.services.agent_stream import stream_agent_run

logger = logging.getLogger(__name__)

router = APIRouter()
manager = AgentConnectionManager()

_REVIEW_PRECREATE_ACTIONS: frozenset[str] = frozenset({"triage", "dpa", "pia", "gap"})
_DSAR_ACTIONS: frozenset[str] = frozenset({"dsar"})
_POLICY_ACTIONS: frozenset[str] = frozenset({"policy_sweep", "policy_query"})

_VALID_ACTIONS: frozenset[str] = _REVIEW_PRECREATE_ACTIONS | _DSAR_ACTIONS | _POLICY_ACTIONS


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
                "提供方和 API Key，再使用个人信息保护技能。"
            ),
            "code": "llm_not_configured",
        },
    )
    return False


async def _run_skill(
    *, websocket: WebSocket, user: User, data: dict[str, Any], action: str
) -> None:
    skill: PrivacySkillName = action  # type: ignore[assignment]
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        await manager.send_event(websocket, "error", {"message": "prompt is required"})
        return
    if not await _require_llm_configured(websocket, user):
        return

    review_type: str | None = SKILL_REVIEW_TYPE.get(skill)
    dsar_id: str | None = None

    # Resolve + ownership-check the DSAR record before running.
    if action in _DSAR_ACTIONS:
        dsar_id = data.get("dsar_id")
        if not dsar_id:
            await manager.send_event(websocket, "error", {"message": "dsar_id is required"})
            return
        with contextmanager(get_db_session)() as db:
            dsar = privacy_dsar_repo.get_by_id(db, dsar_id)
            if dsar is None or dsar.user_id != str(user.id):
                await manager.send_event(
                    websocket, "error", {"message": "DSAR not found or not owned by you"}
                )
                return

    with contextmanager(get_db_session)() as db:
        profile = privacy_profile_repo.get_by_user_id(db, str(user.id))
        profile_md = profile.profile_content if profile else None

        review_id: str | None = None
        if action in _REVIEW_PRECREATE_ACTIONS:
            row = privacy_review_repo.create(
                db,
                user_id=str(user.id),
                review_type=review_type or "triage",
                subject=data.get("subject"),
                status="draft",
            )
            review_id = row.id
            await manager.send_event(websocket, "review_started", {"review_id": review_id})

        agent = create_privacy_agent(
            skill,
            practice_profile_markdown=profile_md,
            **_resolve_user_llm_config(user),
        )
        deps = PrivacyDeps(
            user_id=str(user.id),
            db=db,
            review_type=review_type,
            review_id=review_id,
            dsar_id=dsar_id,
            output_dir=str(Path("outputs") / "privacy" / str(user.id)),
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


@router.websocket("/ws/privacy")
async def privacy_websocket(
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
