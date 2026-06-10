"""Pure-arithmetic IP renewal/maintenance deadline rules (no LLM).

Recomputes each asset's next deadline from its key dates + per-jurisdiction
rules — deadlines are NOT trusted from storage (rules change; a wrong stored
date is worse than none). Used by both the portfolio report/audit endpoints and
the renewal-watcher scheduled task.

Jurisdiction baseline (中国, as of the source plugin's ip-core-rules.md):
  - 商标 (CN): 注册有效期 10 年（自核准注册日），期满前 12 个月续展，6 个月宽展（商标法§40）
  - 发明专利 (CN): 20 年（自申请日）；年费按年缴纳（专利法§42）
  - 实用新型 (CN): 10 年（自申请日）
  - 外观设计 (CN): 15 年（自申请日）
  - 著作权 (CN): 无续展
  - 马德里国际注册: 10 年续展
  - 域名: 按注册商，宽展期因注册商而异（标 unknown 提示人工核实）
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date

_MONTHS_RENEWAL_WINDOW = 12  # 商标续展窗口
_TRADEMARK_GRACE_MONTHS = 6
_PATENT_FEE_GRACE_MONTHS = 6

# Term length (years from the anchor date) per asset_type.
_TERM_YEARS: dict[str, int] = {
    "trademark": 10,
    "patent_invention": 20,
    "patent_utility": 10,
    "patent_design": 15,
}


def _add_years(d: date, years: int) -> date:
    try:
        return d.replace(year=d.year + years)
    except ValueError:  # Feb 29 → Feb 28
        return d.replace(year=d.year + years, day=28)


def _add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


@dataclass
class Deadline:
    deadline_type: str
    due_date: date | None
    grace_end: date | None
    basis_rule: str
    status: str  # upcoming / due_soon / grace / lapsed / unknown


def compute_next_deadline(
    *,
    asset_type: str,
    jurisdiction: str | None,
    status: str,
    filing_date: date | None,
    registration_date: date | None,
    grant_date: date | None,
    agent_managed: bool = False,
    today: date | None = None,
) -> Deadline:
    """Compute the single most-urgent next deadline for one asset."""
    today = today or date.today()
    juris = (jurisdiction or "CN").upper()

    # Copyright has no renewal — surfaced as its own status so the bucketer can
    # skip it rather than mislabel it as "data missing".
    if asset_type == "copyright":
        return Deadline("无续展", None, None, "著作权无需续展", "no_renewal")

    # Madrid international registration (trademarks only) — 10-year renewal.
    if asset_type == "trademark" and ("MADRID" in juris or "马德里" in (jurisdiction or "")):
        if registration_date is None:
            return Deadline("马德里续展", None, None, "缺注册日，无法计算", "unknown")
        due = _add_years(registration_date, 10)
        return _classify("马德里续展", due, _add_months(due, 6), "马德里议定书 10 年续展", today)

    # Domains — registrar-specific; flag for manual check.
    if asset_type == "domain":
        return Deadline("域名续费", None, None, "按注册商规则，请人工核实", "unknown")

    # Trademark — 10yr from registration, renew in final 12 months, 6mo grace.
    if asset_type == "trademark":
        if registration_date is None:
            return Deadline("商标续展", None, None, "缺注册日，无法计算", "unknown")
        due = _add_years(registration_date, 10)
        grace_end = _add_months(due, _TRADEMARK_GRACE_MONTHS)
        return _classify("商标续展", due, grace_end, "商标法§40：10年，6个月宽展", today)

    # Patents — term and annual fees both run from the filing date (申请日) under
    # CN law; grant_date alone cannot place the term, so require filing_date.
    if asset_type in {"patent_invention", "patent_utility", "patent_design"}:
        anchor = filing_date
        if anchor is None:
            return Deadline("专利年费", None, None, "缺申请日，无法计算", "unknown")
        term_years = _TERM_YEARS[asset_type]
        term_end = _add_years(anchor, term_years)
        if today >= term_end:
            return Deadline("专利期限届满", term_end, None, f"专利法：{term_years}年期满", "lapsed")
        # Next annual-fee anniversary.
        next_anniv = anchor
        while next_anniv <= today:
            next_anniv = _add_years(next_anniv, 1)
        grace_end = _add_months(next_anniv, _PATENT_FEE_GRACE_MONTHS)
        return _classify("专利年费", next_anniv, grace_end, "专利法§42-43：年费，6个月宽展", today)

    return Deadline("未知", None, None, "未映射的资产类型", "unknown")


def _classify(
    deadline_type: str, due: date, grace_end: date | None, basis: str, today: date
) -> Deadline:
    if due < today:
        if grace_end is not None and today <= grace_end:
            return Deadline(deadline_type, due, grace_end, basis, "grace")
        return Deadline(deadline_type, due, grace_end, basis, "lapsed")
    return Deadline(
        deadline_type, due, grace_end, basis, "due_soon" if (due - today).days <= 90 else "upcoming"
    )


# --- bucketing for the report / cron ----------------------------------------

_BUCKET_ORDER = ("grace_lapsed", "due_30", "due_60", "due_90", "agent_managed", "unknown")
_BUCKET_PRIORITY = {
    "grace_lapsed": "high",
    "due_30": "high",
    "due_60": "medium",
    "due_90": "medium",
}


@dataclass
class DeadlineBuckets:
    grace_lapsed: list[dict] = field(default_factory=list)
    due_30: list[dict] = field(default_factory=list)
    due_60: list[dict] = field(default_factory=list)
    due_90: list[dict] = field(default_factory=list)
    agent_managed: list[dict] = field(default_factory=list)
    unknown: list[dict] = field(default_factory=list)

    def has_alerts(self) -> bool:
        return bool(self.grace_lapsed or self.due_30 or self.due_60 or self.due_90)

    def top_priority(self) -> str:
        if self.grace_lapsed or self.due_30:
            return "high"
        if self.due_60 or self.due_90:
            return "medium"
        return "low"

    def summary(self) -> str:
        parts = []
        if self.grace_lapsed:
            parts.append(f"{len(self.grace_lapsed)} 项宽展/已失效")
        if self.due_30:
            parts.append(f"{len(self.due_30)} 项30天内")
        if self.due_60:
            parts.append(f"{len(self.due_60)} 项30-60天")
        if self.due_90:
            parts.append(f"{len(self.due_90)} 项60-90天")
        return "；".join(parts) or "无近期到期"

    def to_dict(self) -> dict[str, list[dict]]:
        return {name: getattr(self, name) for name in _BUCKET_ORDER}


def _asset_entry(asset: object, deadline: Deadline) -> dict:
    return {
        "id": getattr(asset, "id", None),
        "asset_type": getattr(asset, "asset_type", None),
        "jurisdiction": getattr(asset, "jurisdiction", None),
        "title": getattr(asset, "title", None),
        "business_owner": getattr(asset, "business_owner", None),
        "deadline_type": deadline.deadline_type,
        "due_date": deadline.due_date.isoformat() if deadline.due_date else None,
        "grace_end": deadline.grace_end.isoformat() if deadline.grace_end else None,
        "basis_rule": deadline.basis_rule,
        "status": deadline.status,
    }


def bucket_assets(assets: list[object], today: date | None = None) -> DeadlineBuckets:
    """Recompute every asset's deadline and bucket it by urgency (pure arithmetic)."""
    today = today or date.today()
    buckets = DeadlineBuckets()
    for asset in assets:
        dl = compute_next_deadline(
            asset_type=getattr(asset, "asset_type", ""),
            jurisdiction=getattr(asset, "jurisdiction", None),
            status=getattr(asset, "status", ""),
            filing_date=getattr(asset, "filing_date", None),
            registration_date=getattr(asset, "registration_date", None),
            grant_date=getattr(asset, "grant_date", None),
            today=today,
        )
        # Assets with no renewal cycle (e.g. copyright) are never surfaced.
        if dl.status == "no_renewal":
            continue
        if getattr(asset, "agent_managed", False):
            buckets.agent_managed.append(_asset_entry(asset, dl))
            continue
        entry = _asset_entry(asset, dl)
        if dl.status in {"grace", "lapsed"}:
            buckets.grace_lapsed.append(entry)
        elif dl.status == "unknown" or dl.due_date is None:
            buckets.unknown.append(entry)
        else:
            days = (dl.due_date - today).days
            if days <= 30:
                buckets.due_30.append(entry)
            elif days <= 60:
                buckets.due_60.append(entry)
            elif days <= 90:
                buckets.due_90.append(entry)
            # >90 days: not surfaced in the alert window.
    return buckets


def render_renewal_report(buckets: DeadlineBuckets) -> str:
    """Markdown report for the in-app notification (no LLM)."""
    lines = ["## IP 组合续展预警", ""]
    sections = [
        ("🔴 宽展期 / 已失效", buckets.grace_lapsed),
        ("⏰ 30 日内到期", buckets.due_30),
        ("🟠 30-60 日内到期", buckets.due_60),
        ("🟡 60-90 日内到期", buckets.due_90),
        ("🌐 代理机构代管", buckets.agent_managed),
        ("❓ 状态不明（数据缺失）", buckets.unknown),
    ]
    for header, items in sections:
        if not items:
            continue
        lines.append(f"**{header}（{len(items)}）**")
        for it in items:
            due = it.get("due_date") or "—"
            lines.append(
                f"- {it.get('title') or it.get('id')} / {it.get('jurisdiction') or '—'}"
                f" — {it.get('deadline_type')}，到期 {due}（{it.get('basis_rule')}）"
            )
        lines.append("")
    lines.append(
        "> 每项期限在提交申请或缴费前，请对照 CNIPA 商标/专利公告或 WIPO 核实。"
        "该期限从登记册推算得出，非系统记录——记录但错误的到期日比未记录更糟。"
    )
    return "\n".join(lines)
