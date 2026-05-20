"""Tests for shared JSON parser."""

import json

import pytest

from app.agents.shared.json_parser import parse_json


class TestParseJson:
    def test_raw_json(self):
        result = parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_markdown_code_block(self):
        text = 'Some text\n```json\n{"key": "value"}\n```\nMore text'
        result = parse_json(text)
        assert result == {"key": "value"}

    def test_markdown_block_without_json_tag(self):
        text = '```\n{"key": "value"}\n```'
        result = parse_json(text)
        assert result == {"key": "value"}

    def test_multiple_code_blocks_takes_first_valid(self):
        text = '```\ninvalid\n```\n```\n{"key": "value"}\n```'
        result = parse_json(text)
        assert result == {"key": "value"}

    def test_mixed_text_with_json_object(self):
        text = 'Here is the analysis:\n{"key": "value"}\nDone.'
        result = parse_json(text)
        assert result == {"key": "value"}

    def test_nested_json(self):
        text = '{"outer": {"inner": "value"}}'
        result = parse_json(text)
        assert result == {"outer": {"inner": "value"}}

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            parse_json("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            parse_json("   ")

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_json("not json at all")

    def test_llm_typical_response(self):
        """Simulate LLM wrapping JSON in markdown with explanation."""
        text = """Based on my analysis, here are the findings:

```json
{
    "findings": [
        {"rule_id": "A1", "level": "low", "finding": "test"}
    ]
}
```

Let me know if you need more details."""
        result = parse_json(text)
        assert "findings" in result
        assert len(result["findings"]) == 1
