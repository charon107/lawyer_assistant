"""Shared PydanticAI streaming kernel for single-shot skill WS runs.

Extracted from ``commercial_ws`` so the streaming / event-forwarding logic can
be unit-tested in isolation and reused by future single-shot skill endpoints
(each WS message = one fresh agent run, no conversation history).

The general ``/ws/agent`` chat handler is deliberately *not* folded in here: it
is conversation-coupled, persists tool calls, and emits a much richer event
vocabulary. Merging the two would force a leaky, parameter-heavy abstraction.

Frontend-facing event vocabulary (unchanged from the original commercial WS):
    text_delta            { content }
    tool_call             { tool_call_id, tool_name, args }
    tool_result           { tool_call_id, content }
    model_request_end     {}                      (FinalResultEvent marker)
    final_result          { output, review_id }
    error                 { message }
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic_ai import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
)
from pydantic_ai.messages import ModelRequest, UserPromptPart

if TYPE_CHECKING:
    from fastapi import WebSocket

    from app.services.agent import AgentConnectionManager

logger = logging.getLogger(__name__)


async def forward_event(
    manager: AgentConnectionManager,
    websocket: WebSocket,
    ev: Any,
) -> None:
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


async def stream_agent_run(
    *,
    manager: AgentConnectionManager,
    websocket: WebSocket,
    agent: Any,
    prompt: str,
    deps: Any,
    review_id: str | None = None,
) -> bool:
    """Drive one agent run, forwarding streamed events. Returns success.

    On failure, sends an ``error`` event and returns False. The caller owns
    the DB session and is responsible for committing tool-side writes.
    """
    try:
        async with agent.iter(
            prompt,
            deps=deps,
            message_history=[ModelRequest(parts=[UserPromptPart(content=prompt)])],
        ) as run:
            async for node in run:
                if hasattr(node, "request") and hasattr(node, "response"):
                    async with node.stream(run.ctx) as event_stream:
                        async for ev in event_stream:
                            await forward_event(manager, websocket, ev)

        final = run.result.output if run.result else ""
        await manager.send_event(
            websocket,
            "final_result",
            {"output": final, "review_id": review_id},
        )
        return True
    except Exception as exc:
        logger.exception("agent run failed for review_id=%s", review_id)
        await manager.send_event(websocket, "error", {"message": str(exc) or "unexpected error"})
        return False
