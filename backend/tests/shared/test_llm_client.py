"""Tests for shared LLM client fixes."""

from unittest.mock import MagicMock, patch

from app.agents.shared.llm_client import LLMClient


class TestLLMClientToolRegistration:
    @patch("openai.OpenAI")
    def test_register_tool_deduplicates_by_name(self, _mock_openai):
        """Registering the same tool name twice should not accumulate."""
        client = LLMClient(api_key="test-key")

        handler1 = MagicMock(return_value="result1")
        handler2 = MagicMock(return_value="result2")

        client.register_tool("my_tool", "desc1", {"type": "object"}, handler1)
        client.register_tool("my_tool", "desc2", {"type": "object"}, handler2)

        assert len(client._tools) == 1
        assert client._tools[0]["description"] == "desc2"
        assert client._tool_handlers["my_tool"] is handler2

    @patch("openai.OpenAI")
    def test_register_multiple_different_tools(self, _mock_openai):
        """Different tool names should all be registered."""
        client = LLMClient(api_key="test-key")

        client.register_tool("tool_a", "desc a", {"type": "object"}, MagicMock())
        client.register_tool("tool_b", "desc b", {"type": "object"}, MagicMock())

        assert len(client._tools) == 2
        assert {t["name"] for t in client._tools} == {"tool_a", "tool_b"}


class TestLLMClientInit:
    @patch("openai.OpenAI")
    def test_creates_client_once(self, mock_openai_cls):
        """OpenAI client should be created in __init__, not per call."""
        client = LLMClient(api_key="test-key", base_url="https://test.com", model="gpt-4")

        mock_openai_cls.assert_called_once_with(
            api_key="test-key", base_url="https://test.com", timeout=120
        )
        assert client._client is not None
