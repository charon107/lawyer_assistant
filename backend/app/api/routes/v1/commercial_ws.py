"""Commercial-legal module WebSocket endpoint.

`/api/v1/commercial/chat` — runs one vendor-agreement-review per WS
session. Simpler than the general agent WS:

- No conversation history across runs; each WS message starts a fresh
  ContractReview row + Agent.
- Tool-call streaming uses the same event names as the general agent
  WS so the frontend chat hook can be cloned with minimal changes.
- Persistence: the review row is created BEFORE the agent runs and
  filled in by the agent's final `write_contract_review` tool call.

Client → Server message:
    {
        "action": "start",
        "review_type": "vendor",            # default
        "side": "purchasing" | "sales",     # falls back to profile.side
        "counterparty": "...",              # optional
        "agreement_name": "...",            # optional
        "annual_value": 100000.0,           # optional
        "contract_text": "<full contract markdown>"  # REQUIRED
    }

Server → Client event types:
    review_started        { review_id }
    text_delta            { content }
    tool_call             { tool_call_id, tool_name, args }
    tool_result           { tool_call_id, content }
    final_result          { output, review_id }
    complete              {}
    error                 { message }
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic_ai import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
)
from pydantic_ai.messages import ModelRequest, UserPromptPart

from app.agents.commercial import (
    CommercialDeps,
    create_commercial_agent,
)
from app.api.deps import get_current_user_ws
from app.db.models.user import User
from app.db.session import get_db_session
from app.repositories import commercial_profile_repo
from app.schemas.commercial.review import ContractReviewCreate
from app.services.agent import AgentConnectionManager
from app.services.contract_review_service import ContractReviewService

logger = logging.getLogger(__name__)

router = APIRouter()
manager = AgentConnectionManager()


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


async def _run_one_review(
    *,
    websocket: WebSocket,
    user: User,
    data: dict[str, Any],
) -> None:
    """Drive one vendor-review from start to finish over `websocket`."""

    contract_text = data.get("contract_text") or ""
    if not contract_text.strip():
        await manager.send_event(
            websocket,
            "error",
            {"message": "contract_text is required and must be non-empty"},
        )
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
            "vendor-agreement-review",
            practice_profile_markdown=profile_md,
            **_resolve_user_llm_config(user),
        )

        deps = CommercialDeps(
            user_id=str(user.id),
            db=db,
            review_id=review_id,
        )

        # 3. Stream the agent.
        try:
            async with agent.iter(
                contract_text,
                deps=deps,
                message_history=[ModelRequest(parts=[UserPromptPart(content=contract_text)])],
            ) as run:
                async for node in run:
                    if hasattr(node, "request") and hasattr(node, "response"):
                        # tool/model node — iterate its events for streaming
                        async with node.stream(run.ctx) as event_stream:
                            async for ev in event_stream:
                                await _forward_event(websocket, ev)
                    # Otherwise it's an end node — handled by run.result below.

            final = run.result.output if run.result else ""
            await manager.send_event(
                websocket,
                "final_result",
                {"output": final, "review_id": review_id},
            )
        except Exception as exc:
            logger.exception("vendor-review run failed for review_id=%s", review_id)
            await manager.send_event(
                websocket, "error", {"message": str(exc) or "unexpected error"}
            )
            return
        finally:
            db.commit()  # persist any tool-side writes

    await manager.send_event(websocket, "complete", {})


async def _forward_event(websocket: WebSocket, ev: Any) -> None:
    """Map a PydanticAI streaming event to a WS event for the frontend."""
    if isinstance(ev, (PartStartEvent, PartDeltaEvent)):
        delta = getattr(ev, "delta", None) or getattr(ev, "part", None)
        if isinstance(delta, TextPartDelta):
            await manager.send_event(websocket, "text_delta", {"content": delta.content_delta})
        return

    if isinstance(ev, FunctionToolCallEvent):
        part = ev.part
        await manager.send_event(
            websocket,
            "tool_call",
            {
                "tool_call_id": part.tool_call_id,
                "tool_name": part.tool_name,
                "args": part.args,
            },
        )
        return

    if isinstance(ev, FunctionToolResultEvent):
        await manager.send_event(
            websocket,
            "tool_result",
            {
                "tool_call_id": ev.tool_call_id,
                "content": str(ev.result.content),
            },
        )
        return

    if isinstance(ev, FinalResultEvent):
        # FinalResultEvent fires before the actual run.result is set on
        # PydanticAI; we surface it as a marker so the frontend can
        # close out the streaming card.
        await manager.send_event(websocket, "model_request_end", {})
        return


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
            if action != "start":
                await manager.send_event(
                    websocket,
                    "error",
                    {"message": f"Unknown action {action!r}; expected 'start'."},
                )
                continue

            await _run_one_review(websocket=websocket, user=user, data=data)
    finally:
        manager.disconnect(websocket)
