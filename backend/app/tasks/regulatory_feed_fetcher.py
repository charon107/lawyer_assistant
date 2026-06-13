"""Feed fetching layer for regulatory-legal (本模块全新基础设施).

Fetches configured RSS/Atom/JSON sources and returns normalized candidates.
Reuses the ``law_fetch`` httpx pattern (timeout + UA + retry). RSS/Atom via
``feedparser`` (lazy-imported so the orchestration is testable without it).

Review decisions baked in:
- A1: every source fetch returns an explicit outcome — ``ok`` / ``empty`` /
  ``error`` (with reason). The cron distinguishes "源返回空(健康)" from "抓取
  失败(坏了)" so a broken monitor never renders as "一切平静".
- P1: ``fetch_unique_sources`` dedups by URL and fetches each unique URL ONCE,
  then the cron fans the parsed result out to every user — a shared gov source
  is never hammered N times.

v1 scope: RSS/Atom + JSON auto-fetch. HTML-only 部委站标"需手动录入"(skip).
``fetch_fn`` is injectable for deterministic tests (no network).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

import httpx
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
_AUTO_FORMATS = frozenset({"rss", "atom", "json"})

# item_type inference by title keyword (确定性，无 LLM).
_TYPE_PATTERNS: list[tuple[str, str]] = [
    ("nprm", r"征求意见|公开征求"),
    ("pre_rule", r"调研|立法计划|起草说明"),
    ("enforcement", r"行政处罚|罚款|处罚决定|查处|立案"),
    ("guidance", r"指引|指南|答记者问|解读|问答"),
    ("speech", r"讲话|致辞|发言"),
    ("settlement", r"和解|整改"),
    ("normative", r"通知|公告|意见|方案"),
    ("regulation", r"决定|办法|规定|条例|规则"),
]

_DATE_RE = re.compile(r"(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})")
_DEADLINE_RE = re.compile(
    r"(?:截止|意见反馈截止|反馈截止)[^\d]{0,8}(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})"
)


@dataclass
class SourceOutcome:
    """Per-source fetch result (A1: ok / empty / error)."""

    status: str  # "ok" | "empty" | "error"
    error: str | None = None
    items: list[dict] = field(default_factory=list)


@dataclass
class UserFetchResult:
    """Aggregated result for one user (consumed by WS fetch_reg_feeds tool)."""

    candidates: list[dict] = field(default_factory=list)
    ok_count: int = 0
    total_count: int = 0
    errored_sources: list[str] = field(default_factory=list)
    empty_sources: list[str] = field(default_factory=list)


def infer_item_type(title: str) -> str:
    """Deterministically infer item_type from a title (no LLM)."""
    for item_type, pattern in _TYPE_PATTERNS:
        if re.search(pattern, title or ""):
            return item_type
    return "other"


def _parse_date(text: str) -> date | None:
    m = _DATE_RE.search(text or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _parse_deadline(text: str) -> date | None:
    m = _DEADLINE_RE.search(text or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def make_dedup_key(*, link: str | None, title: str | None, regulator: str | None) -> str:
    """Stable dedup key: prefer URL, else hash(title+regulator)."""
    if link:
        return hashlib.sha256(link.encode("utf-8")).hexdigest()[:32]
    seed = f"{title or ''}|{regulator or ''}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]


def _normalize_entry(*, title: str, link: str | None, regulator: str, summary: str) -> dict:
    blob = f"{title}\n{summary}"
    return {
        "title": title,
        "link": link,
        "regulator": regulator,
        "summary": summary,
        "item_type": infer_item_type(title),
        "published_date": _parse_date(blob),
        "comment_deadline": _parse_deadline(blob),
        "source_tag": "[联网检索—需复核]",
        "dedup_key": make_dedup_key(link=link, title=title, regulator=regulator),
    }


def _fetch_rss(source: dict) -> SourceOutcome:
    """Fetch + parse an RSS/Atom feed via feedparser (lazy import)."""
    import feedparser  # lazy: keeps orchestration importable/testable without the dep

    url = source.get("url", "")
    regulator = source.get("regulator") or source.get("name") or ""
    try:
        # Fetch bytes with httpx (bounded timeout) — feedparser.parse(url) uses
        # urllib with NO timeout, so a hung feed host would stall the cron thread
        # indefinitely. Hand the fetched content to feedparser instead.
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url, headers=_HEADERS)
            resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
    except Exception as exc:
        return SourceOutcome(status="error", error=f"{type(exc).__name__}: {exc}")
    if getattr(parsed, "bozo", 0) and not parsed.entries:
        return SourceOutcome(
            status="error", error=str(getattr(parsed, "bozo_exception", "parse error"))
        )
    entries = parsed.entries or []
    if not entries:
        return SourceOutcome(status="empty")
    items = [
        _normalize_entry(
            title=(e.get("title") or "").strip(),
            link=e.get("link"),
            regulator=regulator,
            summary=(e.get("summary") or "").strip(),
        )
        for e in entries
        if (e.get("title") or "").strip()
    ]
    return SourceOutcome(status="ok" if items else "empty", items=items)


def _fetch_json(source: dict) -> SourceOutcome:
    """Best-effort JSON-API fetch (generic list-of-entries extraction)."""
    url = source.get("url", "")
    regulator = source.get("regulator") or source.get("name") or ""
    list_key = source.get("list_key")  # optional path to the entries array
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url, headers=_HEADERS)
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:
        return SourceOutcome(status="error", error=f"{type(exc).__name__}: {exc}")

    rows = payload.get(list_key) if (list_key and isinstance(payload, dict)) else payload
    if isinstance(rows, dict):
        rows = rows.get("list") or rows.get("data") or rows.get("items")
    if not isinstance(rows, list) or not rows:
        return SourceOutcome(status="empty")
    items = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        title = str(r.get("title") or r.get("name") or "").strip()
        if not title:
            continue
        items.append(
            _normalize_entry(
                title=title,
                link=r.get("url") or r.get("link"),
                regulator=regulator,
                summary=str(r.get("summary") or r.get("content") or ""),
            )
        )
    return SourceOutcome(status="ok" if items else "empty", items=items)


def _fetch_one(source: dict) -> SourceOutcome:
    """Dispatch a single source by format. HTML-only sources are skipped (manual)."""
    fmt = (source.get("format") or "").lower()
    if fmt in ("rss", "atom"):
        return _fetch_rss(source)
    if fmt == "json":
        return _fetch_json(source)
    # HTML-only / unknown → not auto-fetchable in v1
    return SourceOutcome(status="empty")


FetchFn = Callable[[dict], SourceOutcome]


def fetch_unique_sources(
    sources: list[dict], *, fetch_fn: FetchFn | None = None
) -> dict[str, SourceOutcome]:
    """P1: dedup sources by URL, fetch each unique URL ONCE. Returns url → outcome."""
    fn = fetch_fn or _fetch_one
    seen: dict[str, SourceOutcome] = {}
    for source in sources:
        url = source.get("url")
        if not url or url in seen:
            continue
        if (source.get("format") or "").lower() not in _AUTO_FORMATS:
            continue
        try:
            seen[url] = fn(source)
        except Exception as exc:
            logger.exception("feed fetch failed for %s", url)
            seen[url] = SourceOutcome(status="error", error=str(exc))
    return seen


def _decode_feed_config(raw: str | None) -> list[dict]:
    if not raw:
        return []
    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if isinstance(decoded, dict):
        decoded = decoded.get("sources") or decoded.get("feeds") or []
    return [s for s in decoded if isinstance(s, dict)] if isinstance(decoded, list) else []


def fetch_for_user(
    db: Session, *, user_id: str, fetch_fn: FetchFn | None = None
) -> UserFetchResult:
    """WS path: fetch the user's enabled sources and aggregate (A1 per-source status)."""
    from app.repositories import regulatory_profile_repo

    profile = regulatory_profile_repo.get_by_user_id(db, user_id)
    sources = [
        s
        for s in _decode_feed_config(profile.feed_config if profile else None)
        if s.get("enabled", True) and (s.get("format") or "").lower() in _AUTO_FORMATS
    ]
    outcomes = fetch_unique_sources(sources, fetch_fn=fetch_fn)
    result = UserFetchResult(total_count=len(sources))
    for s in sources:
        outcome = outcomes.get(s.get("url", ""))
        name = s.get("name") or s.get("regulator") or s.get("url", "?")
        if outcome is None or outcome.status == "error":
            result.errored_sources.append(name)
            continue
        result.ok_count += 1
        if outcome.status == "empty":
            result.empty_sources.append(name)
        else:
            result.candidates.extend(outcome.items)
    return result
