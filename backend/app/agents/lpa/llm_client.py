"""
LLM Client with Agent Loop — follows the learn-claude-code architecture.

Core pattern:  messages → model → tools → write-back → loop
"""

import json
import logging
from collections.abc import Callable
from typing import Any

# Default API timeout in seconds
_API_TIMEOUT = 120

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI-compatible client wrapped with agent-loop tool dispatch."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "",
        model: str = "",
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._tools: list[dict[str, Any]] = []
        self._tool_handlers: dict[str, Callable] = {}

    def register_tool(self, name: str, description: str, input_schema: dict, handler: Callable):
        """Register a tool at instance level."""
        self._tools.append(
            {
                "name": name,
                "description": description,
                "input_schema": input_schema,
            }
        )
        self._tool_handlers[name] = handler

    def agent_loop(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        max_turns: int = 10,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """
        Run the agent loop (s01 pattern):
          messages → model → execute tools → write-back → repeat
        """
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key, base_url=self._base_url, timeout=_API_TIMEOUT)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        openai_tools = self._build_openai_tools()

        # ── Log full request context on first turn ──
        logger.info("agent_loop START — model=%s, max_turns=%d", model or self._model, max_turns)
        logger.debug("SYSTEM PROMPT:\n%s", system_prompt)
        logger.debug("USER MESSAGE (first 2000 chars):\n%s", user_message[:2000])
        logger.info("TOOLS (%d registered):", len(openai_tools))
        for t in openai_tools:
            logger.info("  tool: %s — %s", t["function"]["name"], t["function"]["description"][:200])
            logger.debug("  parameters: %s", json.dumps(t["function"].get("parameters", {}), ensure_ascii=False)[:500])

        for turn in range(max_turns):
            used_model = model or self._model
            kwargs = {
                "model": used_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools

            logger.info("--- turn %d ---", turn)
            try:
                resp = client.chat.completions.create(**kwargs)
            except Exception as api_err:
                logger.error("API ERROR: %s: %s", type(api_err).__name__, api_err)
                raise
            choice = resp.choices[0]

            logger.info("RESPONSE finish_reason=%s", choice.finish_reason)
            if choice.message.content:
                logger.debug("RESPONSE content:\n%s", choice.message.content[:2000])
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    logger.info("RESPONSE tool_call: %s(id=%s)", tc.function.name, tc.id)
                    logger.debug("RESPONSE tool_call args: %s", tc.function.arguments)

            if choice.finish_reason == "stop":
                return choice.message.content or ""

            if choice.finish_reason == "tool_calls":
                assistant_msg = choice.message.model_dump()
                messages.append(assistant_msg)

                for tc in choice.message.tool_calls:
                    handler = self._tool_handlers.get(tc.function.name)
                    logger.info("EXECUTING tool: %s (handler=%s)", tc.function.name, handler is not None)
                    if handler is None:
                        result = json.dumps({"error": f"Unknown tool: {tc.function.name}"})
                    else:
                        try:
                            args = json.loads(tc.function.arguments)
                            logger.debug("TOOL args: %s", json.dumps(args, ensure_ascii=False))
                            if not args:
                                logger.warning("TOOL called with EMPTY args!")
                                result = json.dumps({"error": "参数为空。请根据合同内容填写实际值后重新调用工具。"}, ensure_ascii=False)
                            else:
                                result = handler(**args)
                                if not isinstance(result, str):
                                    result = json.dumps(result, ensure_ascii=False)
                                # Return tool result directly — skip model's re-explanation
                                # (works for single-tool patterns like fact extraction)
                                logger.info("TOOL result (len=%d)", len(str(result)))
                                return str(result)
                        except Exception as e:
                            logger.warning("TOOL error: %s", e)
                            result = json.dumps({"error": str(e)})

                    logger.debug("TOOL result (len=%d):\n%s", len(str(result)), str(result)[:1000])
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": str(result),
                        }
                    )
                continue

            # finish_reason is "length" or other — return what we have
            logger.warning("agent_loop unexpected finish_reason=%s, returning content", choice.finish_reason)
            return choice.message.content or ""

        return json.dumps({"error": "Max turns exceeded"}) if self._tool_handlers else ""

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Simple one-shot chat (no tools, no loop)."""
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key, base_url=self._base_url, timeout=_API_TIMEOUT)

        used_model = model or self._model
        logger.info("chat() called, model=%s", used_model)
        try:
            resp = client.chat.completions.create(
                model=used_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as api_err:
            logger.error("chat() API call failed: %s: %s", type(api_err).__name__, api_err)
            raise

        content = resp.choices[0].message.content or ""
        logger.info("chat() response: content_len=%d, finish_reason=%s",
                    len(content), resp.choices[0].finish_reason)
        if content:
            logger.info("chat() content preview: %s", content[:200])
        else:
            logger.warning("chat() returned EMPTY content, finish_reason=%s", resp.choices[0].finish_reason)
        return content

    def _build_openai_tools(self) -> list[dict[str, Any]]:
        """Convert Anthropic-style tool schema to OpenAI function-calling format."""
        result = []
        for tool in self._tools:
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {}),
                    },
                }
            )
        return result
