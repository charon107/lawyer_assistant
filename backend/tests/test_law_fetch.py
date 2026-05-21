"""Tests for app.commands.law_fetch — HTTP, URL building, and HTML parsing."""

from pathlib import Path

import httpx
import pytest

from app.commands.law_fetch import (
    FetchError,
    _build_url,
    _html_to_markdown,
    _preflight_check,
    _request_html,
    fetch_and_save,
)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


# ---------------------------------------------------------------------------
# _request_html
# ---------------------------------------------------------------------------


def test_request_html_returns_body_on_200():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>ok</html>")

    with _client(handler) as client:
        body = _request_html("https://example.invalid/", client)

    assert body == "<html>ok</html>"


def test_request_html_returns_none_on_404():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    with _client(handler) as client:
        body = _request_html("https://example.invalid/", client)

    assert body is None


def test_request_html_retries_on_5xx_then_succeeds(monkeypatch):
    monkeypatch.setattr("app.commands.law_fetch.time.sleep", lambda _s: None)
    calls = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(502, text="bad gateway")
        return httpx.Response(200, text="<html>done</html>")

    with _client(handler) as client:
        body = _request_html("https://example.invalid/", client, attempts=3)

    assert body == "<html>done</html>"
    assert calls["n"] == 3


def test_request_html_returns_none_on_timeout_after_retries(monkeypatch):
    monkeypatch.setattr("app.commands.law_fetch.time.sleep", lambda _s: None)

    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("simulated timeout")

    with _client(handler) as client:
        body = _request_html("https://example.invalid/", client, attempts=2)

    assert body is None


# ---------------------------------------------------------------------------
# _build_url
# ---------------------------------------------------------------------------


def test_build_url_percent_encodes_chinese_title():
    url = _build_url("中华人民共和国民法典")
    assert url.startswith("https://zh.wikisource.org/wiki/")
    # Each character should be percent-encoded into %XX triplets — no raw CJK.
    assert all(ord(c) < 128 for c in url)
    assert "%E6%B0%91%E6%B3%95%E5%85%B8" in url  # 民法典


# ---------------------------------------------------------------------------
# _preflight_check
# ---------------------------------------------------------------------------


def test_preflight_check_passes_when_marker_present():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text='<div class="mw-parser-output">ok</div>')

    with _client(handler) as client:
        _preflight_check(client)  # should not raise


def test_preflight_check_raises_when_unreachable(monkeypatch):
    monkeypatch.setattr("app.commands.law_fetch.time.sleep", lambda _s: None)

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="down")

    with _client(handler) as client, pytest.raises(FetchError, match="unreachable"):
        _preflight_check(client)


def test_preflight_check_raises_when_layout_changed():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>nothing useful</html>")

    with _client(handler) as client, pytest.raises(FetchError, match="layout"):
        _preflight_check(client)


# ---------------------------------------------------------------------------
# _html_to_markdown
# ---------------------------------------------------------------------------


_SAMPLE_HTML = """
<html><body>
<div id="mw-content-text"><div class="mw-parser-output">
<p>题注：本法由全国人大于 2007 年通过。</p>
<h2><span class="mw-headline">第一章　总则</span>
<span class="mw-editsection">[编辑]</span></h2>
<p><b>第一条</b>　为完善劳动合同制度。</p>
<p>劳动合同制度的具体目标。</p>
<p><b>第二条</b>　本法适用于境内用人单位。</p>
<h3><span class="mw-headline">第一节　一般规定</span></h3>
<p><b>第三条</b>　订立劳动合同。</p>
</div></div>
</body></html>
"""


def test_html_to_markdown_emits_title_and_chapters():
    md = _html_to_markdown(_SAMPLE_HTML, law_name="中华人民共和国劳动合同法")
    lines = md.splitlines()
    assert lines[0] == "# 中华人民共和国劳动合同法"
    assert "## 第一章 总则" in lines
    assert "### 第一节 一般规定" in lines


def test_html_to_markdown_strips_edit_markers():
    md = _html_to_markdown(_SAMPLE_HTML, law_name="中华人民共和国劳动合同法")
    assert "[编辑]" not in md


def test_html_to_markdown_joins_continuation_paragraphs_into_one_article_line():
    md = _html_to_markdown(_SAMPLE_HTML, law_name="中华人民共和国劳动合同法")
    article_one = next(ln for ln in md.splitlines() if ln.startswith("第一条"))
    assert "为完善劳动合同制度" in article_one
    assert "劳动合同制度的具体目标" in article_one  # continuation merged


def test_html_to_markdown_skips_preamble_before_first_article():
    md = _html_to_markdown(_SAMPLE_HTML, law_name="中华人民共和国劳动合同法")
    # 题注 should not be attached to any article body
    assert "题注" not in md


def test_html_to_markdown_raises_when_content_missing():
    with pytest.raises(FetchError):
        _html_to_markdown("<html><body>no content</body></html>", law_name="X")


# ---------------------------------------------------------------------------
# fetch_and_save
# ---------------------------------------------------------------------------


def test_fetch_and_save_returns_false_when_below_article_threshold(tmp_path: Path):
    """Sample HTML has only 3 articles — below _MIN_ARTICLES_PER_LAW=5 floor."""

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_SAMPLE_HTML)

    target = {"law_id": "劳动合同法", "wikisource_title": "中华人民共和国劳动合同法"}
    with _client(handler) as client:
        ok = fetch_and_save(target, tmp_path, client)

    assert ok is False
    assert not (tmp_path / "劳动合同法.md").exists()


def test_fetch_and_save_reports_success_when_articles_above_threshold(tmp_path: Path):
    # Build HTML with 6 articles (above the _MIN_ARTICLES_PER_LAW=5 floor).
    arts = "".join(
        f"<p><b>第{n}条</b>　内容{n}。</p>" for n in ["一", "二", "三", "四", "五", "六"]
    )
    html = f"""
    <div id="mw-content-text"><div class="mw-parser-output">
    <h2><span class="mw-headline">第一章　总则</span></h2>
    {arts}
    </div></div>
    """

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    target = {"law_id": "劳动合同法", "wikisource_title": "中华人民共和国劳动合同法"}
    with _client(handler) as client:
        ok = fetch_and_save(target, tmp_path, client)

    assert ok is True
    out = tmp_path / "劳动合同法.md"
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert content.startswith("# 中华人民共和国劳动合同法")
    assert "第一条" in content
    assert "第六条" in content


def test_fetch_and_save_skips_existing_without_force(tmp_path: Path):
    target = {"law_id": "民法典", "wikisource_title": "中华人民共和国民法典"}
    existing = tmp_path / "民法典.md"
    existing.write_text("# old", encoding="utf-8")

    def handler(req: httpx.Request) -> httpx.Response:
        raise AssertionError("HTTP should not be called when file exists")

    with _client(handler) as client:
        ok = fetch_and_save(target, tmp_path, client, force=False)

    assert ok is True
    assert existing.read_text(encoding="utf-8") == "# old"


def test_fetch_and_save_overwrites_when_force(tmp_path: Path):
    arts = "".join(
        f"<p><b>第{n}条</b>　内容{n}。</p>" for n in ["一", "二", "三", "四", "五", "六"]
    )
    html = f"""
    <div id="mw-content-text"><div class="mw-parser-output">
    {arts}
    </div></div>
    """

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    target = {"law_id": "劳动法", "wikisource_title": "中华人民共和国劳动法"}
    out = tmp_path / "劳动法.md"
    out.write_text("# stale", encoding="utf-8")

    with _client(handler) as client:
        ok = fetch_and_save(target, tmp_path, client, force=True)

    assert ok is True
    assert "第一条" in out.read_text(encoding="utf-8")


def test_fetch_and_save_returns_false_on_http_error(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("app.commands.law_fetch.time.sleep", lambda _s: None)

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    target = {"law_id": "未知法", "wikisource_title": "未知法"}
    with _client(handler) as client:
        ok = fetch_and_save(target, tmp_path, client)

    assert ok is False
    assert not (tmp_path / "未知法.md").exists()
