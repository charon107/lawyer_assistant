"""Unit tests for the commercial WebSocket dispatch validation branches.

The streaming agent run itself needs a real LLM and is covered by manual
E2E (same convention as test_routes.py). What we *can* test cheaply are the
pure validation short-circuits that fire before any LLM or DB work:

  - missing / empty contract_text
  - unknown review_type (no skill mapping)
  - missing review_id for a downstream skill
  - the "no LLM configured" guard (never silently falls back)

Each helper sends events through the module-level `manager`. We swap in a
fake WebSocket that records the JSON events instead of touching a socket.
"""

from types import SimpleNamespace
from typing import Any

import pytest

from app.api.routes.v1 import commercial_ws


class _FakeWebSocket:
    """Records send_json payloads; satisfies manager.send_event."""

    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send_json(self, payload: dict[str, Any]) -> None:
        self.sent.append(payload)


def _user(*, with_llm: bool) -> SimpleNamespace:
    llm = [SimpleNamespace(provider="openai", model="m", api_key="k", base_url=None)]
    return SimpleNamespace(id="u-1", llm_configs=llm if with_llm else [])


def _events(ws: _FakeWebSocket) -> list[tuple[str, dict[str, Any]]]:
    return [(e["type"], e["data"]) for e in ws.sent]


class TestRunOneReviewValidation:
    @pytest.mark.anyio
    async def test_missing_contract_text_errors(self):
        ws = _FakeWebSocket()
        await commercial_ws._run_one_review(
            websocket=ws,  # type: ignore[arg-type]
            user=_user(with_llm=True),  # type: ignore[arg-type]
            data={"review_type": "vendor"},
        )
        types = [t for t, _ in _events(ws)]
        assert types == ["error"]
        assert "contract_text" in ws.sent[0]["data"]["message"]

    @pytest.mark.anyio
    async def test_unknown_review_type_errors(self):
        ws = _FakeWebSocket()
        await commercial_ws._run_one_review(
            websocket=ws,  # type: ignore[arg-type]
            user=_user(with_llm=True),  # type: ignore[arg-type]
            data={"review_type": "bogus", "contract_text": "x"},
        )
        assert _events(ws)[0][0] == "error"
        assert "Unknown review_type" in ws.sent[0]["data"]["message"]

    @pytest.mark.anyio
    async def test_no_llm_config_blocks_with_code(self):
        ws = _FakeWebSocket()
        await commercial_ws._run_one_review(
            websocket=ws,  # type: ignore[arg-type]
            user=_user(with_llm=False),  # type: ignore[arg-type]
            data={"review_type": "nda", "contract_text": "x"},
        )
        assert ws.sent[0]["data"]["code"] == "llm_not_configured"


class TestRunDownstreamSkillValidation:
    @pytest.mark.anyio
    async def test_missing_review_id_errors(self):
        ws = _FakeWebSocket()
        await commercial_ws._run_downstream_skill(
            websocket=ws,  # type: ignore[arg-type]
            user=_user(with_llm=True),  # type: ignore[arg-type]
            data={},
            action="summarize",
        )
        assert _events(ws)[0][0] == "error"
        assert "review_id" in ws.sent[0]["data"]["message"]

    @pytest.mark.anyio
    async def test_no_llm_config_blocks(self):
        ws = _FakeWebSocket()
        await commercial_ws._run_downstream_skill(
            websocket=ws,  # type: ignore[arg-type]
            user=_user(with_llm=False),  # type: ignore[arg-type]
            data={"review_id": "r-1"},
            action="escalate",
        )
        assert ws.sent[0]["data"]["code"] == "llm_not_configured"


def test_skill_maps_cover_expected_types():
    assert set(commercial_ws._SKILL_BY_REVIEW_TYPE) == {"vendor", "nda", "saas"}
    assert set(commercial_ws._SKILL_BY_ACTION) == {"summarize", "escalate"}
