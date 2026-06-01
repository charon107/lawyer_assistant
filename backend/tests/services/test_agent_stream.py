"""Characterization tests for the shared streaming kernel.

`app.services.agent_stream` was extracted verbatim from the commercial WS
handler so the event-forwarding / run-driving logic could be unit-tested in
isolation. These tests lock in the *current* behavior (event-name mapping,
happy path, error path, empty result) before any further refactor.

We build real PydanticAI event instances so the ``isinstance`` dispatch in
``forward_event`` exercises the same branches it does in production. The
agent run itself is faked: a ``FakeRun`` async-CM/async-iterator yields a
model-request node (has ``request``/``response`` + ``.stream``) and a
non-model node (lacks them) so we can assert the node filter.
"""

from typing import Any

import pytest
from pydantic_ai import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
)
from pydantic_ai.messages import TextPart, ToolCallPart, ToolReturnPart

from app.services.agent_stream import forward_event, stream_agent_run


class _FakeManager:
    """Records send_event(websocket, event_type, data) calls."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    async def send_event(self, _ws: Any, event_type: str, data: dict[str, Any]) -> bool:
        self.events.append((event_type, data))
        return True


# ---------------------------------------------------------------------------
# forward_event — event-name mapping
# ---------------------------------------------------------------------------


class TestForwardEvent:
    @pytest.mark.anyio
    async def test_text_part_delta_maps_to_text_delta(self) -> None:
        mgr = _FakeManager()
        ev = PartDeltaEvent(index=0, delta=TextPartDelta(content_delta="hello"))
        await forward_event(mgr, object(), ev)
        assert mgr.events == [("text_delta", {"content": "hello"})]

    @pytest.mark.anyio
    async def test_part_start_with_text_part_emits_nothing(self) -> None:
        # PartStartEvent carries a TextPart (not a TextPartDelta) → no event.
        mgr = _FakeManager()
        ev = PartStartEvent(index=0, part=TextPart(content="hi"))
        await forward_event(mgr, object(), ev)
        assert mgr.events == []

    @pytest.mark.anyio
    async def test_tool_call_event_maps_to_tool_call(self) -> None:
        mgr = _FakeManager()
        part = ToolCallPart("my_tool", {"a": 1}, tool_call_id="tc-1")
        await forward_event(mgr, object(), FunctionToolCallEvent(part=part))
        assert mgr.events == [
            ("tool_call", {"tool_call_id": "tc-1", "tool_name": "my_tool", "args": {"a": 1}})
        ]

    @pytest.mark.anyio
    async def test_tool_result_event_maps_to_tool_result(self) -> None:
        mgr = _FakeManager()
        ret = ToolReturnPart("my_tool", "done", tool_call_id="tc-1")
        await forward_event(mgr, object(), FunctionToolResultEvent(result=ret))
        assert mgr.events == [("tool_result", {"tool_call_id": "tc-1", "content": "done"})]

    @pytest.mark.anyio
    async def test_final_result_event_maps_to_model_request_end(self) -> None:
        mgr = _FakeManager()
        await forward_event(mgr, object(), FinalResultEvent(tool_name=None, tool_call_id=None))
        assert mgr.events == [("model_request_end", {})]


# ---------------------------------------------------------------------------
# Fakes for stream_agent_run
# ---------------------------------------------------------------------------


class _FakeEventStream:
    """async-CM yielding a fixed list of events."""

    def __init__(self, events: list[Any]) -> None:
        self._events = events

    async def __aenter__(self) -> "_FakeEventStream":
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        return None

    async def __aiter__(self) -> Any:
        for ev in self._events:
            yield ev


class _ModelNode:
    """A model-request node: has request/response + .stream(ctx)."""

    request = object()
    response = object()

    def __init__(self, events: list[Any]) -> None:
        self._events = events

    def stream(self, _ctx: Any) -> _FakeEventStream:
        return _FakeEventStream(self._events)


class _NonModelNode:
    """A node that is NOT a model request (no request/response attrs)."""


class _FakeResult:
    def __init__(self, output: str) -> None:
        self.output = output


class _FakeRun:
    """async-CM + async-iterator over nodes; exposes .ctx and .result."""

    def __init__(self, nodes: list[Any], result: _FakeResult | None) -> None:
        self._nodes = nodes
        self.ctx = object()
        self.result = result

    async def __aenter__(self) -> "_FakeRun":
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        return None

    async def __aiter__(self) -> Any:
        for node in self._nodes:
            yield node


class _FakeAgent:
    def __init__(self, run: _FakeRun) -> None:
        self._run = run
        self.iter_kwargs: dict[str, Any] = {}

    def iter(self, prompt: str, **kwargs: Any) -> _FakeRun:
        self.iter_kwargs = {"prompt": prompt, **kwargs}
        return self._run


class _RaisingAgent:
    def iter(self, *_a: Any, **_k: Any) -> Any:
        raise RuntimeError("boom")


# ---------------------------------------------------------------------------
# stream_agent_run — happy path, node filter, error, empty result
# ---------------------------------------------------------------------------


class TestStreamAgentRun:
    @pytest.mark.anyio
    async def test_happy_path_streams_events_and_final_result(self) -> None:
        mgr = _FakeManager()
        events = [
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta="hi")),
            FunctionToolCallEvent(part=ToolCallPart("t", {}, tool_call_id="c1")),
        ]
        run = _FakeRun(nodes=[_ModelNode(events)], result=_FakeResult("OUTPUT"))
        agent = _FakeAgent(run)

        ok = await stream_agent_run(
            manager=mgr,  # type: ignore[arg-type]
            websocket=object(),  # type: ignore[arg-type]
            agent=agent,
            prompt="contract",
            deps=object(),
            review_id="r-1",
        )

        assert ok is True
        assert mgr.events == [
            ("text_delta", {"content": "hi"}),
            ("tool_call", {"tool_call_id": "c1", "tool_name": "t", "args": {}}),
            ("final_result", {"output": "OUTPUT", "review_id": "r-1"}),
        ]

    @pytest.mark.anyio
    async def test_non_model_nodes_are_skipped(self) -> None:
        mgr = _FakeManager()
        events = [PartDeltaEvent(index=0, delta=TextPartDelta(content_delta="x"))]
        run = _FakeRun(
            nodes=[_NonModelNode(), _ModelNode(events)],
            result=_FakeResult("done"),
        )
        ok = await stream_agent_run(
            manager=mgr,  # type: ignore[arg-type]
            websocket=object(),  # type: ignore[arg-type]
            agent=_FakeAgent(run),
            prompt="p",
            deps=object(),
            review_id="r-2",
        )
        assert ok is True
        # Only the model node's single text_delta + the final_result.
        assert mgr.events == [
            ("text_delta", {"content": "x"}),
            ("final_result", {"output": "done", "review_id": "r-2"}),
        ]

    @pytest.mark.anyio
    async def test_empty_result_yields_empty_output(self) -> None:
        mgr = _FakeManager()
        run = _FakeRun(nodes=[], result=None)
        ok = await stream_agent_run(
            manager=mgr,  # type: ignore[arg-type]
            websocket=object(),  # type: ignore[arg-type]
            agent=_FakeAgent(run),
            prompt="p",
            deps=object(),
            review_id="r-3",
        )
        assert ok is True
        assert mgr.events == [("final_result", {"output": "", "review_id": "r-3"})]

    @pytest.mark.anyio
    async def test_exception_sends_error_and_returns_false(self) -> None:
        mgr = _FakeManager()
        ok = await stream_agent_run(
            manager=mgr,  # type: ignore[arg-type]
            websocket=object(),  # type: ignore[arg-type]
            agent=_RaisingAgent(),
            prompt="p",
            deps=object(),
            review_id="r-4",
        )
        assert ok is False
        assert mgr.events == [("error", {"message": "boom"})]
