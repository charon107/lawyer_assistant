"""Crawler for flk.npc.gov.cn — downloads Chinese law full texts as markdown.

Usage (via law_db.py CLI):
    uv run law-db fetch                          # download all 17 laws
    uv run law-db fetch --source /tmp/laws       # custom output dir
    uv run law-db fetch --force                  # overwrite existing files
"""

import logging
import re
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from app.commands import error, info, success, warning

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Target law list (covers all 8 skill domains)
# ---------------------------------------------------------------------------

LAW_TARGETS: list[dict[str, str]] = [
    # 民法
    {"keyword": "中华人民共和国民法典", "law_id": "民法典", "type": "law"},
    # 劳动法
    {"keyword": "中华人民共和国劳动合同法", "law_id": "劳动合同法", "type": "law"},
    {"keyword": "中华人民共和国劳动法", "law_id": "劳动法", "type": "law"},
    {"keyword": "中华人民共和国社会保险法", "law_id": "社会保险法", "type": "law"},
    # 商法
    {"keyword": "中华人民共和国公司法", "law_id": "公司法", "type": "law"},
    {"keyword": "中华人民共和国合伙企业法", "law_id": "合伙企业法", "type": "law"},
    # 知识产权
    {"keyword": "中华人民共和国著作权法", "law_id": "著作权法", "type": "law"},
    {"keyword": "中华人民共和国专利法", "law_id": "专利法", "type": "law"},
    {"keyword": "中华人民共和国商标法", "law_id": "商标法", "type": "law"},
    # 行政法
    {"keyword": "中华人民共和国行政许可法", "law_id": "行政许可法", "type": "law"},
    {"keyword": "中华人民共和国行政处罚法", "law_id": "行政处罚法", "type": "law"},
    {"keyword": "中华人民共和国行政复议法", "law_id": "行政复议法", "type": "law"},
    {"keyword": "中华人民共和国行政诉讼法", "law_id": "行政诉讼法", "type": "law"},
    # 刑法
    {"keyword": "中华人民共和国刑法", "law_id": "刑法", "type": "law"},
    # 保密法
    {"keyword": "中华人民共和国保守国家秘密法", "law_id": "保守国家秘密法", "type": "law"},
    # 社会法
    {"keyword": "中华人民共和国就业促进法", "law_id": "就业促进法", "type": "law"},
    # 行政法规
    {"keyword": "工伤保险条例", "law_id": "工伤保险条例", "type": "regulation"},
]

_BASE_URL = "https://flk.npc.gov.cn"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LexMind/1.0; legal-research-bot)",
    "Accept": "application/json",
    "Referer": "https://flk.npc.gov.cn/",
}

# Article number regex: 第一条, 第一百零二条, 第一条之一 ...
_ARTICLE_RE = re.compile(r"^第[零一二三四五六七八九十百千]+条(?:之[零一二三四五六七八九]+)?")
_CHAPTER_RE = re.compile(r"^第[零一二三四五六七八九十]+(?:编|章)\s*")
_SECTION_RE = re.compile(r"^第[零一二三四五六七八九十]+节\s*")


def _search_law(keyword: str, law_type: str, client: httpx.Client) -> dict | None:
    """Search flk.npc.gov.cn and return best matching entry."""
    params = {
        "type": law_type,
        "searchType": "title",
        "keyword": keyword,
        "sortTp": "0",
        "page": "1",
        "pageSize": "10",
    }
    try:
        resp = client.get(f"{_BASE_URL}/api/", params=params, headers=_HEADERS)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Search failed for %r: %s", keyword, e)
        return None

    items: list[dict] = []
    result = data.get("result", {})
    if isinstance(result, dict):
        items = result.get("data", [])
    elif isinstance(result, list):
        items = result

    if not items:
        return None

    # Prefer exact title match (keyword contained in title), then most recent
    candidates = [it for it in items if keyword in it.get("title", "")]
    if not candidates:
        candidates = items
    # Sort by publish date descending (most recent first)
    candidates.sort(key=lambda x: x.get("publish", "") or "", reverse=True)
    return candidates[0]


def _fetch_detail(entry_id: str, client: httpx.Client) -> str | None:
    """Fetch HTML body from /api/detail?id=..."""
    try:
        resp = client.get(
            f"{_BASE_URL}/api/detail",
            params={"id": entry_id},
            headers=_HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning("Detail fetch failed for id=%s: %s", entry_id, e)
        return None

    result = data.get("result", {})
    if isinstance(result, dict):
        return result.get("body") or result.get("content")
    return None


def _clean_text(text: str) -> str:
    """Normalize whitespace in law text."""
    text = text.replace("　", " ")  # full-width space → regular space
    text = text.replace("\xa0", " ")  # &nbsp;
    text = re.sub(r" {2,}", " ", text)  # collapse multiple spaces
    return text.strip()


def _html_to_markdown(html: str, law_name: str) -> str:
    """Convert flk.npc.gov.cn HTML body to parser.py-compatible markdown."""
    soup = BeautifulSoup(html, "html.parser")

    lines: list[str] = [f"# {law_name}", ""]
    current_paragraph: list[str] = []

    def flush_paragraph() -> None:
        if current_paragraph:
            lines.append(" ".join(current_paragraph))
            lines.append("")
            current_paragraph.clear()

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "div"]):
        # Skip nested tags (only process top-level children)
        if tag.parent and tag.parent.name in ("p", "li", "span", "td"):
            continue

        raw = _clean_text(tag.get_text(separator=" "))
        if not raw:
            continue

        tag_name = tag.name

        if tag_name in ("h1", "h2"):
            flush_paragraph()
            if _CHAPTER_RE.match(raw) or raw != law_name:
                lines.append(f"## {raw}")
                lines.append("")

        elif tag_name == "h3":
            flush_paragraph()
            if _SECTION_RE.match(raw):
                lines.append(f"### {raw}")
            else:
                lines.append(f"### {raw}")
            lines.append("")

        elif tag_name in ("p", "div"):
            # Detect chapter / section headings hiding inside <p> tags
            if _CHAPTER_RE.match(raw):
                flush_paragraph()
                lines.append(f"## {raw}")
                lines.append("")
            elif _SECTION_RE.match(raw):
                flush_paragraph()
                lines.append(f"### {raw}")
                lines.append("")
            elif _ARTICLE_RE.match(raw):
                flush_paragraph()
                current_paragraph.append(raw)
            else:
                # Continuation text (preamble, supplementary clauses, etc.)
                if current_paragraph:
                    current_paragraph.append(raw)
                # else: skip leading preamble text that has no article prefix

    flush_paragraph()

    # Collapse excessive blank lines (max 1 blank line between elements)
    result_lines: list[str] = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        result_lines.append(line)
        prev_blank = is_blank

    return "\n".join(result_lines)


def fetch_and_save(
    target: dict[str, str], output_dir: Path, client: httpx.Client, force: bool = False
) -> bool:
    """Download one law, convert to markdown, save to {law_id}.md. Returns True on success."""
    law_id = target["law_id"]
    keyword = target["keyword"]
    law_type = target.get("type", "law")
    out_file = output_dir / f"{law_id}.md"

    if out_file.exists() and not force:
        info(f"  {law_id}: already exists, skipping (use --force to overwrite)")
        return True

    info(f"  Searching: {keyword} ...")
    entry = _search_law(keyword, law_type, client)
    if not entry:
        warning(f"  {law_id}: not found on flk.npc.gov.cn — skipping")
        return False

    law_name = _clean_text(entry.get("title", keyword))
    entry_id = entry.get("id") or entry.get("no")
    if not entry_id:
        warning(f"  {law_id}: no ID in search result — skipping")
        return False

    info(f"  Fetching: {law_name} (id={entry_id}) ...")
    html = _fetch_detail(str(entry_id), client)
    if not html:
        warning(f"  {law_id}: failed to fetch full text — skipping")
        return False

    markdown = _html_to_markdown(html, law_name)

    # Basic sanity check — should have at least 10 article lines
    article_lines = [ln for ln in markdown.splitlines() if _ARTICLE_RE.match(ln.strip())]
    if len(article_lines) < 5:
        warning(
            f"  {law_id}: only {len(article_lines)} articles parsed, HTML structure may have changed"
        )

    out_file.write_text(markdown, encoding="utf-8")
    success(f"  {law_id}: saved {len(article_lines)} articles → {out_file}")
    return True


def run_fetch(output: Path, force: bool = False) -> None:
    """Download all target laws from flk.npc.gov.cn to output directory."""
    output.mkdir(parents=True, exist_ok=True)
    info(f"Output directory: {output.resolve()}")

    ok = 0
    fail = 0
    with httpx.Client(timeout=30, follow_redirects=True) as client:
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
            time.sleep(1.5)  # be polite to the government server

    success(f"\nFetch complete: {ok} succeeded, {fail} failed.")
    if ok > 0:
        info(f"Next step: uv run law-db import --source {output}")
