"""
LLM Client with Agent Loop — follows the learn-claude-code architecture.

Core pattern:  messages → model → tools → write-back → loop
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

TOOL_HANDLERS: Dict[str, Callable] = {}
TOOLS: List[Dict[str, Any]] = []


def register_tool(name: str, description: str, input_schema: dict, handler: Callable):
    """Register a tool + its handler (follows s02 pattern)."""
    TOOLS.append({
        "name": name,
        "description": description,
        "input_schema": input_schema,
    })
    TOOL_HANDLERS[name] = handler


class LLMClient:
    """OpenAI-compatible client wrapped with agent-loop tool dispatch."""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self._api_key = api_key
        self._base_url = base_url
        self._tools: List[Dict[str, Any]] = []
        self._tool_handlers: Dict[str, Callable] = {}

    def register_tool(self, name: str, description: str, input_schema: dict, handler: Callable):
        """Register a tool at instance level."""
        self._tools.append({
            "name": name,
            "description": description,
            "input_schema": input_schema,
        })
        self._tool_handlers[name] = handler

    def agent_loop(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        max_turns: int = 10,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """
        Run the agent loop (s01 pattern):
          messages → model → execute tools → write-back → repeat
        """
        from openai import OpenAI
        client = OpenAI(api_key=self._api_key, base_url=self._base_url)

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        openai_tools = self._build_openai_tools()

        for turn in range(max_turns):
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools

            resp = client.chat.completions.create(**kwargs)
            choice = resp.choices[0]

            if choice.finish_reason == "stop":
                return choice.message.content or ""

            if choice.finish_reason == "tool_calls":
                assistant_msg = choice.message.model_dump()
                messages.append(assistant_msg)

                for tc in choice.message.tool_calls:
                    handler = self._tool_handlers.get(tc.function.name) or TOOL_HANDLERS.get(tc.function.name)
                    if handler is None:
                        result = json.dumps({"error": f"Unknown tool: {tc.function.name}"})
                    else:
                        try:
                            args = json.loads(tc.function.arguments)
                            result = handler(**args)
                            if not isinstance(result, str):
                                result = json.dumps(result, ensure_ascii=False)
                        except Exception as e:
                            result = json.dumps({"error": str(e)})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": str(result),
                    })
                continue

            # finish_reason is "length" or other — return what we have
            return choice.message.content or ""

        return json.dumps({"error": "Max turns exceeded"}) if TOOL_HANDLERS else ""

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Simple one-shot chat (no tools, no loop)."""
        from openai import OpenAI
        client = OpenAI(api_key=self._api_key, base_url=self._base_url)

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    def _build_openai_tools(self) -> List[Dict[str, Any]]:
        """Convert Anthropic-style tool schema to OpenAI function-calling format."""
        result = []
        for tool in self._tools or TOOLS:
            result.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {}),
                },
            })
        return result
