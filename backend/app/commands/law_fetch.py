"""Crawler for zh.wikisource.org — downloads Chinese law full texts as markdown.

Usage (via law_db.py CLI):
    uv run law-db fetch                          # download all 17 laws
    uv run law-db fetch --source /tmp/laws       # custom output dir
    uv run law-db fetch --force                  # overwrite existing files

Source note:
    Originally targeted flk.npc.gov.cn, but that site migrated to a SPA whose
    new API no longer exposes article body text (only a chapter/article title
    tree). Wikisource hosts stable HTML versions of all major Chinese laws and
    is freely accessible, so we fetch from there and convert to the markdown
    format consumed by ``app.services.law_data.parser``.
"""

from __future__ import annotations

import logging
import re
import time
import urllib.parse
from pathlib import Path

import httpx
from bs4 import BeautifulSoup, Tag

from app.commands import error, info, success, warning

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Target law list (covers all 8 skill domains)
# ---------------------------------------------------------------------------
# ``wikisource_title`` is the page slug under https://zh.wikisource.org/wiki/.
# The page must contain the full article text inline (verified for all entries).

LAW_TARGETS: list[dict[str, str]] = [
    # 民法
    {"law_id": "民法典", "wikisource_title": "中华人民共和国民法典", "type": "law"},
    # 劳动法
    {"law_id": "劳动合同法", "wikisource_title": "中华人民共和国劳动合同法", "type": "law"},
    {"law_id": "劳动法", "wikisource_title": "中华人民共和国劳动法", "type": "law"},
    {"law_id": "社会保险法", "wikisource_title": "中华人民共和国社会保险法", "type": "law"},
    # 商法
    {"law_id": "公司法", "wikisource_title": "中华人民共和国公司法", "type": "law"},
    {"law_id": "合伙企业法", "wikisource_title": "中华人民共和国合伙企业法", "type": "law"},
    # 知识产权
    {"law_id": "著作权法", "wikisource_title": "中华人民共和国著作权法", "type": "law"},
    {"law_id": "专利法", "wikisource_title": "中华人民共和国专利法", "type": "law"},
    {"law_id": "商标法", "wikisource_title": "中华人民共和国商标法", "type": "law"},
    # 行政法
    {"law_id": "行政许可法", "wikisource_title": "中华人民共和国行政许可法", "type": "law"},
    {"law_id": "行政处罚法", "wikisource_title": "中华人民共和国行政处罚法", "type": "law"},
    {"law_id": "行政复议法", "wikisource_title": "中华人民共和国行政复议法", "type": "law"},
    {"law_id": "行政诉讼法", "wikisource_title": "中华人民共和国行政诉讼法", "type": "law"},
    # 刑法
    {"law_id": "刑法", "wikisource_title": "中华人民共和国刑法", "type": "law"},
    # 保密法
    {
        "law_id": "保守国家秘密法",
        "wikisource_title": "中华人民共和国保守国家秘密法",
        "type": "law",
    },
    # 社会法
    {"law_id": "就业促进法", "wikisource_title": "中华人民共和国就业促进法", "type": "law"},
    # 行政法规
    {"law_id": "工伤保险条例", "wikisource_title": "工伤保险条例", "type": "regulation"},
]

_BASE_URL = "https://zh.wikisource.org"
_PAGE_URL_TEMPLATE = _BASE_URL + "/wiki/{slug}"
_PREFLIGHT_TITLE = "中华人民共和国宪法"  # stable, never going away
_MIN_ARTICLES_PER_LAW = 5  # sanity floor; if fewer parsed, warn

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LexMind/1.0; +https://lexmind.example)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
}

# Structural regex used while walking the parsed HTML
_ARTICLE_RE = re.compile(r"^第[零一二三四五六七八九十百千]+条(?:之[零一二三四五六七八九十百千]+)?")
_CHAPTER_RE = re.compile(r"^第[零一二三四五六七八九十百千]+(?:编|章)(?:\s|$|[一-鿿])")
_SECTION_RE = re.compile(r"^第[零一二三四五六七八九十百千]+节(?:\s|$|[一-鿿])")
_EDIT_TAG = "[编辑]"


class FetchError(RuntimeError):
    """Raised when the upstream source cannot be reached or parsed."""


def _request_html(url: str, client: httpx.Client, *, attempts: int = 3) -> str | None:
    """GET an HTML page with retry on transient failures.

    Returns the decoded body on HTTP 200, otherwise ``None``. Logs context on
    every failure so callers can surface useful diagnostics.
    """
    for attempt in range(1, attempts + 1):
        try:
            resp = client.get(url, headers=_HEADERS)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            logger.warning(
                "Network error fetching %s (attempt %d/%d): %s",
                url,
                attempt,
                attempts,
                exc,
            )
            if attempt < attempts:
                time.sleep(2 * attempt)
                continue
            return None

        if resp.status_code >= 500 and attempt < attempts:
            logger.warning(
                "Upstream %s returned HTTP %d (attempt %d/%d), retrying.",
                url,
                resp.status_code,
                attempt,
                attempts,
            )
            time.sleep(2 * attempt)
            continue

        if resp.status_code != 200:
            body_snippet = resp.text[:200].replace("\n", " ")
            logger.warning("Unexpected HTTP %d from %s: %s", resp.status_code, url, body_snippet)
            return None

        return resp.text
    return None


def _build_url(wikisource_title: str) -> str:
    """Construct the canonical Wikisource page URL for a Chinese title."""
    slug = urllib.parse.quote(wikisource_title, safe="")
    return _PAGE_URL_TEMPLATE.format(slug=slug)


def _preflight_check(client: httpx.Client) -> None:
    """Verify zh.wikisource.org is reachable before iterating all targets."""
    info("Preflight: testing zh.wikisource.org reachability...")
    html = _request_html(_build_url(_PREFLIGHT_TITLE), client, attempts=1)
    if html is None:
        raise FetchError(
            "Preflight failed: zh.wikisource.org is unreachable. "
            "Check your network connectivity (the site is not behind a firewall, "
            "but DNS or routing may be blocking it)."
        )
    if "mw-parser-output" not in html:
        raise FetchError(
            "Preflight failed: zh.wikisource.org returned an unexpected page "
            "structure (mw-parser-output marker missing). The site layout may "
            "have changed — please update law_fetch.py."
        )
    success("Preflight OK: Wikisource is reachable.")


def _clean_text(text: str) -> str:
    """Normalize whitespace in law text."""
    text = text.replace("　", " ")  # ideographic space → regular space
    text = text.replace("\xa0", " ")  # &nbsp;
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _strip_edit_markers(tag: Tag) -> None:
    """Remove ``<span class="mw-editsection">[编辑]</span>`` decorations in-place."""
    for ed in tag.find_all("span", class_="mw-editsection"):
        ed.decompose()


def _extract_content_root(soup: BeautifulSoup) -> Tag | None:
    """Locate the article body div, skipping the ``textquality`` placeholder.

    Wikisource pages have TWO ``mw-parser-output`` divs:
      1. A small placeholder containing only ``<span id="textquality">``.
      2. The real article body inside ``<div id="mw-content-text">``.

    We always pick the one nested under ``mw-content-text`` to avoid that trap.
    """
    container = soup.find("div", id="mw-content-text")
    if container is None:
        # Fallback: largest mw-parser-output by text length.
        candidates = soup.find_all("div", class_="mw-parser-output")
        if not candidates:
            return None
        return max(candidates, key=lambda d: len(d.get_text() or ""))
    body = container.find("div", class_="mw-parser-output")
    return body if isinstance(body, Tag) else container


def _html_to_markdown(html: str, law_name: str) -> str:
    """Convert a Wikisource law page into parser.py-compatible markdown.

    Output format::

        # 法律名称
        ## 第一章 总则
        ### 第一节 一般规定
        第一条 ...
        第二条 ...
    """
    soup = BeautifulSoup(html, "html.parser")
    root = _extract_content_root(soup)
    if root is None:
        raise FetchError("could not locate article body in Wikisource HTML")

    _strip_edit_markers(root)

    lines: list[str] = [f"# {law_name}", ""]
    current_article: list[str] = []
    seen_first_article = False

    def flush_article() -> None:
        if current_article:
            lines.append(" ".join(current_article))
            lines.append("")
            current_article.clear()

    for tag in root.find_all(["h1", "h2", "h3", "h4", "h5", "p", "dl", "dd"], recursive=True):
        # Skip nested headers — we only want top-level structural elements.
        if tag.parent is not None and tag.parent.name in {"p", "li", "td", "span"}:
            continue
        raw = _clean_text(tag.get_text(separator=" "))
        if not raw or raw == _EDIT_TAG:
            continue
        # The ``[编辑]`` marker can sometimes survive ``_strip_edit_markers``
        # when it lives outside the ``mw-editsection`` span (rare). Trim it.
        if raw.endswith(_EDIT_TAG):
            raw = raw[: -len(_EDIT_TAG)].rstrip()

        name = tag.name

        if name in {"h1", "h2", "h3", "h4", "h5"}:
            if _CHAPTER_RE.match(raw):
                flush_article()
                lines.append(f"## {raw}")
                lines.append("")
            elif _SECTION_RE.match(raw):
                flush_article()
                lines.append(f"### {raw}")
                lines.append("")
            # Other headings (题注/目录/参见/参考文献/外部链接 etc.) are skipped.
            continue

        # <p>, <dl>, <dd> — article body or chapter heading hiding inside.
        if _CHAPTER_RE.match(raw):
            flush_article()
            lines.append(f"## {raw}")
            lines.append("")
            continue
        if _SECTION_RE.match(raw):
            flush_article()
            lines.append(f"### {raw}")
            lines.append("")
            continue
        if _ARTICLE_RE.match(raw):
            flush_article()
            # parser.py expects ``第X条`` followed by whitespace + body.
            current_article.append(raw)
            seen_first_article = True
        else:
            if seen_first_article and current_article:
                current_article.append(raw)
            # else: pre-article preamble (题注/施行说明) — skip silently.

    flush_article()

    # Collapse runs of blank lines.
    result: list[str] = []
    prev_blank = False
    for line in lines:
        blank = not line.strip()
        if blank and prev_blank:
            continue
        result.append(line)
        prev_blank = blank
    return "\n".join(result).rstrip() + "\n"


def fetch_and_save(
    target: dict[str, str],
    output_dir: Path,
    client: httpx.Client,
    force: bool = False,
) -> bool:
    """Download one law, convert to markdown, save to ``{law_id}.md``."""
    law_id = target["law_id"]
    title = target["wikisource_title"]
    out_file = output_dir / f"{law_id}.md"

    if out_file.exists() and not force:
        info(f"  {law_id}: already exists, skipping (use --force to overwrite)")
        return True

    url = _build_url(title)
    info(f"  Fetching: {title} ...")
    html = _request_html(url, client)
    if html is None:
        warning(f"  {law_id}: failed to fetch {url}")
        return False

    try:
        markdown = _html_to_markdown(
            html,
            law_name=f"中华人民共和国{law_id}" if title.startswith("中华人民共和国") else title,
        )
    except FetchError as exc:
        warning(f"  {law_id}: parse failure — {exc}")
        return False

    article_lines = [ln for ln in markdown.splitlines() if _ARTICLE_RE.match(ln.strip())]
    if len(article_lines) < _MIN_ARTICLES_PER_LAW:
        warning(
            f"  {law_id}: only {len(article_lines)} articles parsed — "
            f"Wikisource HTML structure may have changed."
        )
        return False

    out_file.write_text(markdown, encoding="utf-8")
    success(f"  {law_id}: saved {len(article_lines)} articles → {out_file}")
    return True


def run_fetch(output: Path, force: bool = False) -> None:
    """Download all target laws from Wikisource to ``output`` directory."""
    output.mkdir(parents=True, exist_ok=True)
    info(f"Output directory: {output.resolve()}")

    ok = 0
    fail = 0
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        try:
            _preflight_check(client)
        except FetchError as exc:
            error(str(exc))
            raise SystemExit(2) from exc

        for target in LAW_TARGETS:
            try:
                if fetch_and_save(target, output, client, force=force):
                    ok += 1
                else:
                    fail += 1
            except Exception:
                logger.exception("Unexpected error fetching %s", target["law_id"])
                error(f"  {target['law_id']}: unexpected error (see logs)")
                fail += 1
            time.sleep(1.0)  # be polite to Wikimedia

    success(f"\nFetch complete: {ok} succeeded, {fail} failed.")
    if ok > 0:
        info(f"Next step: uv run law-db import --source {output}")
