"""Tests for app.commands.law_fetch — HTTP handling and IP-block detection."""

import httpx
import pytest

from app.commands.law_fetch import IPBlockedError, _request_json


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_request_json_returns_parsed_json_on_200():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": {"data": [{"id": "1"}]}})

    with _client(handler) as client:
        data = _request_json("https://example.invalid/api/", {"q": "x"}, client)

    assert data == {"result": {"data": [{"id": "1"}]}}


def test_request_json_raises_ip_blocked_on_403_allowlist():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="Host not in allowlist")

    with _client(handler) as client, pytest.raises(IPBlockedError):
        _request_json("https://example.invalid/api/", {}, client)


def test_request_json_returns_none_on_non_json_body():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    with _client(handler) as client:
        data = _request_json("https://example.invalid/api/", {}, client)

    assert data is None


def test_request_json_returns_none_on_404():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    with _client(handler) as client:
        data = _request_json("https://example.invalid/api/", {}, client)

    assert data is None


def test_request_json_retries_on_5xx_then_succeeds():
    calls = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(502, text="bad gateway")
        return httpx.Response(200, json={"ok": True})

    with _client(handler) as client:
        data = _request_json("https://example.invalid/api/", {}, client, attempts=3)

    assert data == {"ok": True}
    assert calls["n"] == 3


def test_request_json_returns_none_on_timeout_after_retries():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("simulated timeout")

    with _client(handler) as client:
        data = _request_json("https://example.invalid/api/", {}, client, attempts=2)

    assert data is None


def test_request_json_does_not_raise_ip_blocked_on_other_403():
    """403 without 'allowlist' text should be a normal failure, not an IPBlockedError."""

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="forbidden: invalid api key")

    with _client(handler) as client:
        data = _request_json("https://example.invalid/api/", {}, client)

    assert data is None
