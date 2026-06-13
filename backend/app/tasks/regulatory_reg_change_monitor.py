"""reg-change-monitor scheduled task (regulatory-legal) — 本模块定时代理.

Weekly, DETERMINISTIC (no LLM, no external send). For every configured user:
fetch RSS/Atom/JSON sources → dedup → pre-bucket by materiality (确定性规则) →
auto-register 征求意见稿 as comment periods → write an in-app digest.

This is the module's biggest deviation from the source agent (which runs LLM
policy-diff inline and pushes 飞书). Per design decision §12.3 the cron stays
pure-arithmetic; deep analysis is on-demand via the WS skills.

Review decisions encoded here:
- P1: sources are deduped across all users and each unique URL fetched ONCE.
- A1: per-source ok/empty/error is surfaced in the digest; "一切平静" only when
  no source errored AND nothing new. The feed-check watermark advances only when
  no source errored (failed source's window is retried next run).
- A2: the digest LISTS 🔴 + 🟡 items (counts only 🟢), so a keyword-misbucketed
  real 🔴 can never silently vanish into a number.

Entry point ``run(db)`` is invoked by the scheduler wrapper which owns the
session + commit.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.db.models.regulatory_profile import RegulatoryProfile
from app.repositories import (
    regulatory_comment_repo,
    regulatory_gap_repo,
    regulatory_notification_repo,
    regulatory_profile_repo,
    regulatory_reg_item_repo,
)
from app.tasks import regulatory_feed_fetcher
from app.tasks._common import iter_active_user_ids
from app.tasks.regulatory_materiality_rules import classify_materiality

logger = logging.getLogger(__name__)

_AUTO_FORMATS = frozenset({"rss", "atom", "json"})
_COMMENT_TYPES = frozenset({"nprm", "pre_rule"})


def _as_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return decoded if isinstance(decoded, list) else []


def _extract_keywords(profile: RegulatoryProfile) -> tuple[set[str], set[str], set[str]]:
    """Derive (watchlist_regulators, industry_keywords, practice_keywords) from the profile."""
    watch_regs: set[str] = set()
    for entry in _as_list(getattr(profile, "watchlist", None)):
        if isinstance(entry, dict):
            name = entry.get("机构") or entry.get("regulator") or entry.get("name")
            if name:
                watch_regs.add(str(name))
        elif isinstance(entry, str):
            watch_regs.add(entry)

    industry: set[str] = set()
    practice: set[str] = set()
    raw_threshold = getattr(profile, "materiality_threshold", None)
    if raw_threshold:
        try:
            th = json.loads(raw_threshold)
        except (json.JSONDecodeError, TypeError):
            th = {}
        if isinstance(th, dict):
            industry = {str(k) for k in (th.get("industry_keywords") or th.get("always") or [])}
            practice = {str(k) for k in (th.get("practice_keywords") or th.get("review") or [])}
    return watch_regs, industry, practice


def _user_sources(profile: RegulatoryProfile) -> list[dict]:
    return [
        s
        for s in _as_list(getattr(profile, "feed_config", None))
        if isinstance(s, dict)
        and s.get("enabled", True)
        and (s.get("format") or "").lower() in _AUTO_FORMATS
    ]


@dataclass
class _Digest:
    new_always: list[tuple]  # (item, candidate)
    new_review: list[tuple]
    fyi_count: int
    ok_count: int
    total: int
    errored: list[str]
    open_gap_count: int

    def all_calm(self) -> bool:
        # A1: calm only when nothing errored AND nothing new.
        return (
            not self.errored and not self.new_always and not self.new_review and self.fyi_count == 0
        )

    def priority(self) -> str:
        if self.new_always or self.errored:
            return "high"
        if self.new_review:
            return "medium"
        return "low"

    def summary(self) -> str:
        if self.all_calm():
            return "一切平静（无新增）"
        return f"🔴{len(self.new_always)} 🟡{len(self.new_review)} 🟢{self.fyi_count}"

    def markdown(self) -> str:
        lines = ["# 法规动态简报", ""]
        # A1 source health line
        health = f"**源健康：{self.ok_count}/{self.total} 成功**"
        if self.errored:
            health += f"；⚠️ 失败：{', '.join(self.errored)}（已保留水位线，下次重试）"
        lines.append(health)
        lines.append(f"**开放合规差距：{self.open_gap_count}**")
        lines.append("")
        if self.all_calm():
            lines.append("本周无新增法规动态，监测源全部正常。")
            return "\n".join(lines)
        # A2: list 🔴 + 🟡, count 🟢
        if self.new_always:
            lines.append("## 🔴 始终重要（建议运行 policy-diff）")
            for item, c in self.new_always:
                lines.append(
                    f"- **{c.get('title', '—')}** | {c.get('regulator', '—')} "
                    f"| {c.get('item_type', 'other')} | {item.source_tag or '—'}"
                )
            lines.append("")
        if self.new_review:
            lines.append("## 🟡 值得审阅")
            for _item, c in self.new_review:
                lines.append(
                    f"- {c.get('title', '—')} | {c.get('regulator', '—')} "
                    f"| {c.get('item_type', 'other')}"
                )
            lines.append("")
        if self.fyi_count:
            lines.append(f"## 🟢 仅供参考：{self.fyi_count} 条（详见动态列表）")
        return "\n".join(lines)


def run(db: Session, *, fetch_fn: regulatory_feed_fetcher.FetchFn | None = None) -> int:
    """Run reg-change-monitor for all configured users. Returns digests written."""
    # Gather configured users + their sources.
    users: list[tuple[str, RegulatoryProfile, list[dict]]] = []
    all_sources: list[dict] = []
    for user_id in iter_active_user_ids(db):
        profile = regulatory_profile_repo.get_by_user_id(db, user_id)
        if profile is None or profile.setup_status != "completed":
            continue
        sources = _user_sources(profile)
        users.append((user_id, profile, sources))
        all_sources.extend(sources)

    # P1: fetch each unique URL once across all users.
    outcomes = regulatory_feed_fetcher.fetch_unique_sources(all_sources, fetch_fn=fetch_fn)

    written = 0
    for user_id, profile, sources in users:
        # A1: assemble candidates + per-source status.
        candidates: list[dict] = []
        ok_count = 0
        errored: list[str] = []
        for s in sources:
            outcome = outcomes.get(s.get("url", ""))
            name = s.get("name") or s.get("regulator") or s.get("url", "?")
            if outcome is None or outcome.status == "error":
                errored.append(name)
                continue
            ok_count += 1
            if outcome.status == "ok":
                candidates.extend(outcome.items)

        watch_regs, industry_kw, practice_kw = _extract_keywords(profile)

        new_always: list[tuple] = []
        new_review: list[tuple] = []
        fyi_count = 0
        seen_keys: set[str] = set()  # within-run dedup (same item syndicated on 2 sources)
        for c in candidates:
            dedup_key = c.get("dedup_key")
            if dedup_key and (
                dedup_key in seen_keys
                or regulatory_reg_item_repo.find_by_dedup_key(
                    db, user_id=user_id, dedup_key=dedup_key
                )
            ):
                continue
            if dedup_key:
                seen_keys.add(dedup_key)
            materiality = classify_materiality(
                item_type=c.get("item_type", "other"),
                regulator=c.get("regulator"),
                text=f"{c.get('title', '')} {c.get('summary', '')}",
                watchlist_regulators=watch_regs,
                industry_keywords=industry_kw,
                practice_keywords=practice_kw,
            )
            item = regulatory_reg_item_repo.create(
                db,
                user_id=user_id,
                title=c.get("title"),
                regulator=c.get("regulator"),
                item_type=c.get("item_type", "other"),
                materiality=materiality,
                materiality_source="auto_rule",
                summary=c.get("summary"),
                link=c.get("link"),
                published_date=c.get("published_date"),
                comment_deadline=c.get("comment_deadline"),
                source_tag=c.get("source_tag"),
                source_name=c.get("regulator"),
                dedup_key=dedup_key,
                status="new",
            )
            if materiality == "always":
                new_always.append((item, c))
            elif materiality == "review":
                new_review.append((item, c))
            else:
                fyi_count += 1

            # Auto-register 征求意见稿 as a comment period.
            if c.get("item_type") in _COMMENT_TYPES and c.get("comment_deadline"):
                regulatory_comment_repo.create(
                    db,
                    user_id=user_id,
                    reg_item_id=item.id,
                    regulation=c.get("title"),
                    regulator=c.get("regulator"),
                    summary=c.get("summary"),
                    link=c.get("link"),
                    comment_deadline=c.get("comment_deadline"),
                    detected=date.today(),
                    decision="undecided",
                )

        # A1: advance watermark only when no source errored (failed window retried next run).
        if not errored:
            regulatory_profile_repo.set_last_feed_check(db, profile=profile, ts=datetime.now(UTC))

        open_gaps = regulatory_gap_repo.list_open(db, user_id=user_id)
        digest = _Digest(
            new_always=new_always,
            new_review=new_review,
            fyi_count=fyi_count,
            ok_count=ok_count,
            total=len(sources),
            errored=errored,
            open_gap_count=len(open_gaps),
        )
        # No silent pass — always emit a digest (even "一切平静").
        regulatory_notification_repo.create(
            db,
            user_id=user_id,
            notification_type="reg_digest",
            priority=digest.priority(),
            title=f"法规动态简报：{digest.summary()}",
            content=digest.markdown(),
            action_url="/regulatory/feed",
        )
        written += 1

    logger.info("regulatory_reg_change_monitor wrote %d digests", written)
    return written
