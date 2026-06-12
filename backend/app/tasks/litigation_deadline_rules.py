"""Pure-arithmetic litigation deadline bucketing (no LLM).

Buckets the deadline dates **already stored** on matter events (event_type=
deadline, due_date) and the legal_hold next_refresh dates, by urgency. It does
NOT recompute due_dates from filing_date — the審限 rules below are the reference
used when events are *created* (by matter-update / the model), not here. Stored
deadlines are treated as 线索 (leads), never as authoritative diary entries: the
docket report explicitly tells the lawyer to verify.

Chinese civil procedure reference (for event creation, not recomputed here):
  - 一审普通程序: 6 months (可延长) · 简易程序: 3 months · 小额诉讼: 2 months
  - 上诉期: 判决 15 days / 裁定 10 days · 举证期限: ≥15 days
  - 管辖权异议: 答辩期内 (15 days) · 申请执行时效: 2 years (民诉法§246)
  - 证据保全刷新: 6 months · 诉讼时效: 3 years (民法典§188); 中断重算 (§195)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any

# Bucket field names match their semantic window (no more misleading due_7/due_30).
_BUCKET_ORDER = ("urgent", "due_8_30", "due_31_90", "status_change", "info")


@dataclass
class DocketBuckets:
    """Deadline alert buckets. Field names == their day window."""

    urgent: list[dict[str, Any]] = field(default_factory=list)  # 逾期 / ≤7日
    due_8_30: list[dict[str, Any]] = field(default_factory=list)  # 8-30日
    due_31_90: list[dict[str, Any]] = field(default_factory=list)  # 31-90日
    status_change: list[dict[str, Any]] = field(default_factory=list)  # 近期态势变化
    info: list[dict[str, Any]] = field(default_factory=list)  # 无紧迫事项

    def has_alerts(self) -> bool:
        return bool(self.urgent or self.due_8_30 or self.due_31_90 or self.status_change)

    def top_priority(self) -> str:
        if self.urgent:
            return "high"
        if self.due_8_30 or self.due_31_90:
            return "medium"
        return "low"

    def summary(self) -> str:
        parts: list[str] = []
        if self.urgent:
            parts.append(f"{len(self.urgent)} 项逾期/7日内")
        if self.due_8_30:
            parts.append(f"{len(self.due_8_30)} 项8-30日")
        if self.due_31_90:
            parts.append(f"{len(self.due_31_90)} 项31-90日")
        if self.status_change:
            parts.append(f"{len(self.status_change)} 项态势变化")
        return "；".join(parts) or "无紧急事项"

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        return {name: getattr(self, name) for name in _BUCKET_ORDER}


def bucket_deadlines(
    events: list[Any],  # list of LitigationMatterEvent (deadline type)
    legal_holds: list[Any],  # list of LitigationAnalysis (legal_hold type)
    today: date | None = None,
) -> DocketBuckets:
    """扫描 deadline 事件 + legal_hold next_refresh，按到期窗口分桶（纯算术）。"""
    today = today or date.today()
    buckets = DocketBuckets()

    for ev in events:
        if ev.due_date is None or ev.deadline_status == "met":
            continue  # 已结清的期限不再告警
        days_left = (ev.due_date - today).days
        entry: dict[str, Any] = {
            "matter_id": ev.matter_id,
            "event_id": ev.id,
            "due_date": ev.due_date.isoformat(),
            "summary": ev.summary or "",
            "type": "deadline",
        }

        if days_left < 0:
            entry["label"] = "🔴 已逾期"
            buckets.urgent.append(entry)
        elif days_left <= 7:
            entry["label"] = "🔴 ≤7日"
            buckets.urgent.append(entry)
        elif days_left <= 30:
            entry["label"] = "🟠 8-30日"
            buckets.due_8_30.append(entry)
        elif days_left <= 90:
            entry["label"] = "🔵 31-90日"
            buckets.due_31_90.append(entry)

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
        if (next_refresh - today).days <= 30:
            buckets.due_8_30.append(
                {
                    "matter_id": lh.matter_id,
                    "analysis_id": lh.id,
                    "due_date": next_refresh_str,
                    "summary": f"证据保全刷新到期: {lh.subject or '—'}",
                    "label": "🔵 保全刷新",
                    "type": "legal_hold",
                }
            )

    return buckets


def add_status_changes(buckets: DocketBuckets, recent_events: list[Any]) -> None:
    """把近期非期限事件（裁定/开庭/风险重评估等）填入态势变化桶。"""
    for ev in recent_events:
        buckets.status_change.append(
            {
                "matter_id": ev.matter_id,
                "event_id": ev.id,
                "event_type": ev.event_type,
                "summary": ev.summary or "",
                "label": "📊 态势变化",
                "type": "status_change",
            }
        )


def render_docket_report(buckets: DocketBuckets) -> str:
    """Markdown report for the in-app notification (no LLM)."""
    lines = ["## 案件进度提醒", ""]
    sections = [
        ("🔴 逾期 / 7日内", buckets.urgent),
        ("🟠 8-30日内到期", buckets.due_8_30),
        ("🔵 31-90日内到期", buckets.due_31_90),
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

    if not buckets.has_alerts():
        lines.append("✅ 本周无紧急案件事项。")

    lines.append("")
    lines.append(
        "> ⚠️ 推算期限是**线索非日程**——须律师核实后确认。"
        "不信赖自身文书分类。「无新进」≠「无问题」。不触碰已结案件。"
    )
    return "\n".join(lines)
