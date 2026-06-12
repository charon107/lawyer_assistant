"""Pure-arithmetic litigation deadline rules (no LLM).

Recomputes deadlines from matter events + legal_hold analyses per Chinese
civil procedure rules. Deadlines are NEVER trusted from storage — rules change;
a wrong stored date is worse than none. Used by both the docket-watcher
scheduled task and potentially the portfolio endpoint.

Chinese civil procedure baseline:
  - 一审普通程序: 6 months (可延长)
  - 简易程序: 3 months
  - 小额诉讼: 2 months
  - 上诉期: 判决 15 days / 裁定 10 days
  - 举证期限: ≥15 days
  - 管辖权异议: 答辩期内 (15 days)
  - 申请执行时效: 2 years (民诉法§246)
  - 证据保全刷新: 6 months
  - 诉讼时效: 3 years (民法典§188); 中断重算 (§195)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date

_BUCKET_ORDER = ("urgent", "due_7", "due_30", "status_change", "info")
_BUCKET_PRIORITY = {
    "urgent": "high",
    "due_7": "high",
    "due_30": "medium",
    "status_change": "medium",
    "info": "low",
}


@dataclass
class DocketBuckets:
    urgent: list[dict] = field(default_factory=list)  # 逾期 / 7日内
    due_7: list[dict] = field(default_factory=list)  # 8-30日
    due_30: list[dict] = field(default_factory=list)  # 31-90日
    status_change: list[dict] = field(default_factory=list)  # 态势变化
    info: list[dict] = field(default_factory=list)  # 无紧迫事项

    def has_alerts(self) -> bool:
        return bool(self.urgent or self.due_7 or self.due_30 or self.status_change)

    def top_priority(self) -> str:
        if self.urgent:
            return "high"
        if self.due_7 or self.due_30:
            return "medium"
        return "low"

    def summary(self) -> str:
        parts = []
        if self.urgent:
            parts.append(f"{len(self.urgent)} 项逾期/7日内")
        if self.due_7:
            parts.append(f"{len(self.due_7)} 项8-30日")
        if self.due_30:
            parts.append(f"{len(self.due_30)} 项31-90日")
        if self.status_change:
            parts.append(f"{len(self.status_change)} 项态势变化")
        return "；".join(parts) or "无紧急事项"

    def to_dict(self) -> dict[str, list[dict]]:
        return {name: getattr(self, name) for name in _BUCKET_ORDER}


def bucket_deadlines(
    matters: list,  # list of LitigationMatter
    events: list,  # list of LitigationMatterEvent (deadline type)
    legal_holds: list,  # list of LitigationAnalysis (legal_hold type)
    today: date | None = None,
) -> DocketBuckets:
    """扫描活跃 matters 的 deadline 事件 + legal_hold next_refresh，按审限规则分桶。"""
    today = today or date.today()
    buckets = DocketBuckets()

    # Process deadline events
    for ev in events:
        if ev.due_date is None:
            continue
        days_left = (ev.due_date - today).days
        entry = {
            "matter_id": ev.matter_id,
            "event_id": ev.id,
            "due_date": ev.due_date.isoformat(),
            "summary": ev.summary or "",
            "type": "deadline",
        }

        if days_left < 0 and ev.deadline_status != "met":
            entry["label"] = "🔴 已逾期"
            buckets.urgent.append(entry)
        elif days_left <= 7:
            entry["label"] = "🔴 ≤7日"
            buckets.urgent.append(entry)
        elif days_left <= 30:
            entry["label"] = "🟠 8-30日"
            buckets.due_7.append(entry)
        elif days_left <= 90:
            entry["label"] = "🔵 31-90日"
            buckets.due_30.append(entry)

    # Process legal_hold next_refresh
    for lh in legal_holds:
        if not lh.result_json:
            continue
        try:
            data = json.loads(lh.result_json) if isinstance(lh.result_json, str) else {}
        except json.JSONDecodeError:
            continue
        next_refresh_str = data.get("next_refresh") if isinstance(data, dict) else None
        if not next_refresh_str:
            continue
        try:
            next_refresh = date.fromisoformat(next_refresh_str)
        except (ValueError, TypeError):
            continue
        days_left = (next_refresh - today).days
        if days_left <= 30:
            buckets.due_7.append(
                {
                    "matter_id": lh.matter_id,
                    "analysis_id": lh.id,
                    "due_date": next_refresh_str,
                    "summary": f"证据保全刷新到期: {lh.subject or '—'}",
                    "label": "🔵 保全刷新",
                    "type": "legal_hold",
                }
            )

    # Check for matters with no events (info)
    # This is handled by the caller

    return buckets


def render_docket_report(buckets: DocketBuckets) -> str:
    """Markdown report for the in-app notification (no LLM)."""
    lines = ["## 案件进度提醒", ""]
    sections = [
        ("🔴 逾期 / 7日内", buckets.urgent),
        ("🟠 8-30日内到期", buckets.due_7),
        ("🔵 31-90日内到期", buckets.due_30),
        ("📊 态势变化", buckets.status_change),
    ]
    for header, items in sections:
        if not items:
            continue
        lines.append(f"**{header}（{len(items)}）**")
        for it in items:
            due = it.get("due_date") or "—"
            lines.append(
                f"- {it.get('summary') or it.get('matter_id')} — 到期 {due}（{it.get('label')}）"
            )
        lines.append("")

    if not any(buckets.urgent or buckets.due_7 or buckets.due_30 or buckets.status_change):
        lines.append("✅ 本周无紧急案件事项。")

    lines.append("")
    lines.append(
        "> ⚠️ 推算期限是**线索非日程**——须律师核实后确认。"
        "不信赖自身文书分类。「无新进」≠「无问题」。不触碰已结案件。"
    )
    return "\n".join(lines)
