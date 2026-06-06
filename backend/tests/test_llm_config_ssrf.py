"""SSRF protection for user-supplied LLM ``base_url``.

The LLM config schemas (``LLMConfigCreate`` / ``LLMConfigUpdate``) accept a
user-controlled ``base_url`` that is later used by the OpenAI client to make
server-side requests. Without validation a user could point it at cloud
metadata (``169.254.169.254``) or internal hosts (SSRF).

These tests assert the schema layer rejects internal/loopback/metadata targets
via ``app.core.sanitize.validate_webhook_url`` and accepts public endpoints.
IP literals are used so the validator short-circuits before DNS — keeping the
tests deterministic and offline-safe.
"""

import pytest
from pydantic import ValidationError

from app.schemas.user import LLMConfigCreate, LLMConfigUpdate

BLOCKED_BASE_URLS = [
    "http://169.254.169.254/latest/meta-data/",  # cloud metadata
    "http://100.100.100.200/",  # Alibaba Cloud metadata (CGNAT)
    "http://127.0.0.1:11434",  # loopback (local Ollama)
    "http://10.0.0.5:8000/v1",  # RFC1918 private
    "http://192.168.1.10/v1",  # RFC1918 private
    "ftp://example.com/x",  # disallowed scheme
    "http://user:pass@8.8.8.8/v1",  # credentials in URL
]

ALLOWED_BASE_URLS = [
    "https://8.8.8.8/v1",  # public IP literal — no DNS, passes
    None,  # optional field — skipped
    "",  # empty — skipped
]


class TestLLMConfigCreateSSRF:
    @pytest.mark.parametrize("url", BLOCKED_BASE_URLS)
    def test_blocked_base_url_rejected(self, url: str):
        with pytest.raises(ValidationError):
            LLMConfigCreate(provider="openai", base_url=url)

    @pytest.mark.parametrize("url", ALLOWED_BASE_URLS)
    def test_allowed_base_url_accepted(self, url):
        cfg = LLMConfigCreate(provider="openai", base_url=url)
        assert cfg.base_url == url


class TestLLMConfigUpdateSSRF:
    @pytest.mark.parametrize("url", BLOCKED_BASE_URLS)
    def test_blocked_base_url_rejected(self, url: str):
        with pytest.raises(ValidationError):
            LLMConfigUpdate(base_url=url)

    @pytest.mark.parametrize("url", ALLOWED_BASE_URLS)
    def test_allowed_base_url_accepted(self, url):
        cfg = LLMConfigUpdate(base_url=url)
        assert cfg.base_url == url
