"""Unified JSON parser for LLM responses.

Handles markdown code blocks, mixed text, and raw JSON.
"""

import json
import re


def parse_json(text: str) -> dict:
    """Extract a JSON object from an LLM response string.

    Three-level fallback:
    1. Extract from markdown code blocks (iterate all, try each)
    2. Regex-match the outermost {...} in mixed text
    3. json.loads the full text

    Raises:
        ValueError: If text is empty.
        json.JSONDecodeError: If no valid JSON is found.
    """
    text = text.strip()
    if not text:
        raise ValueError("Empty response from LLM")

    # 1. Markdown code blocks
    if "```" in text:
        blocks = re.findall(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        for block in blocks:
            block = block.strip()
            if block:
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    continue

    # 2. Regex match JSON object in mixed text
    json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # 3. Full text
    return json.loads(text)
