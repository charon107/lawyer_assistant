"""Investigation tools for the employment-legal agent (inv_add/query/memo/summary)."""

import json
from datetime import date
from typing import Any

from pydantic_ai import RunContext

from app.agents.employment.deps import EmploymentDeps
from app.db.models.employment_investigation import EmploymentInvestigation
from app.repositories import employment_investigation_repo as inv_repo

_ENTRY_FIELDS = {
    "entry_type",
    "date_of_event",
    "source",
    "source_type",
    "issues",
    "significance",
    "summary",
    "quote",
    "contradicts_entry_seq",
    "corroborates_entry_seq",
    "pull_criterion",
}


def _load_owned_investigation(deps: EmploymentDeps) -> EmploymentInvestigation:
    if deps.investigation_id is None:
        raise RuntimeError(
            "EmploymentDeps.investigation_id is None — the handler must resolve the "
            "active investigation before running this skill."
        )
    inv = inv_repo.get_by_id(deps.db, deps.investigation_id)
    if inv is None or inv.user_id != deps.user_id:
        raise PermissionError(f"Cannot access investigation {deps.investigation_id}.")
    return inv


async def read_investigation_log(ctx: RunContext[EmploymentDeps]) -> str:
    """读取当前调查的结构化日志（每条带 entry_seq / 类型 / 显著性 / 矛盾-印证链）。

    Returns:
        JSON 字符串。
    """
    inv = _load_owned_investigation(ctx.deps)
    entries = inv_repo.list_log_entries(ctx.deps.db, investigation_id=inv.id)
    items = [
        {
            "entry_seq": e.entry_seq,
            "entry_type": e.entry_type,
            "date_of_event": e.date_of_event.isoformat() if e.date_of_event else None,
            "source": e.source,
            "source_type": e.source_type,
            "significance": e.significance,
            "summary": e.summary,
            "quote": e.quote,
            "contradicts_entry_seq": e.contradicts_entry_seq,
            "corroborates_entry_seq": e.corroborates_entry_seq,
        }
        for e in entries
    ]
    return json.dumps(
        {"investigation": inv.investigation_name, "total": len(items), "entries": items},
        ensure_ascii=False,
    )


async def read_sources(ctx: RunContext[EmploymentDeps]) -> str:
    """读取当前调查的来源清单（用于覆盖缺口分析）。"""
    inv = _load_owned_investigation(ctx.deps)
    rows = inv_repo.list_sources(ctx.deps.db, investigation_id=inv.id)
    items = [
        {"seq": r.source_seq, "source": r.source, "status": r.status, "notes": r.notes}
        for r in rows
    ]
    return json.dumps({"total": len(items), "sources": items}, ensure_ascii=False)


async def read_gaps(ctx: RunContext[EmploymentDeps]) -> str:
    """读取当前调查的证据缺口。"""
    inv = _load_owned_investigation(ctx.deps)
    rows = inv_repo.list_gaps(ctx.deps.db, investigation_id=inv.id)
    items = [
        {"seq": r.gap_seq, "description": r.description, "priority": r.priority, "status": r.status}
        for r in rows
    ]
    return json.dumps({"total": len(items), "gaps": items}, ensure_ascii=False)


def _coerce_entry(raw: dict[str, Any]) -> dict[str, Any]:
    fields = {k: v for k, v in raw.items() if k in _ENTRY_FIELDS and v is not None}
    dov = fields.get("date_of_event")
    if isinstance(dov, str):
        try:
            fields["date_of_event"] = date.fromisoformat(dov)
        except ValueError:
            fields.pop("date_of_event", None)
    issues = fields.get("issues")
    if isinstance(issues, list):
        fields["issues"] = json.dumps(issues, ensure_ascii=False)
    return fields


async def append_log_entries(ctx: RunContext[EmploymentDeps], entries: list[dict[str, Any]]) -> str:
    """把一批调查日志条目写入当前调查（inv_add 文档 needle-finding 命中项调用）。

    Args:
        entries: 条目列表。每项可含 entry_type/date_of_event(ISO)/source/source_type/
            issues(列表)/significance(high|medium|background)/summary/quote/
            pull_criterion/contradicts_entry_seq/corroborates_entry_seq。

    Returns:
        JSON 字符串，含写入的 entry_seq 列表。
    """
    inv = _load_owned_investigation(ctx.deps)
    written: list[int] = []
    for raw in entries:
        entry = inv_repo.append_log_entry(
            ctx.deps.db,
            investigation_id=inv.id,
            privilege="attorney-work-product",
            **_coerce_entry(raw),
        )
        written.append(entry.entry_seq)
    return json.dumps({"written": written, "count": len(written)}, ensure_ascii=False)


async def save_investigation_memo(ctx: RunContext[EmploymentDeps], memo_markdown: str) -> str:
    """保存/更新当前调查的备忘录（inv_memo 调用）。"""
    inv = _load_owned_investigation(ctx.deps)
    inv_repo.update(ctx.deps.db, investigation=inv, memo=memo_markdown, status="memo_draft")
    return json.dumps({"investigation_id": inv.id, "saved": True}, ensure_ascii=False)


async def read_memo(ctx: RunContext[EmploymentDeps]) -> str:
    """读取当前调查的备忘录（inv_summary 据此生成受众摘要）。"""
    inv = _load_owned_investigation(ctx.deps)
    return json.dumps(
        {"investigation": inv.investigation_name, "memo": inv.memo}, ensure_ascii=False
    )
