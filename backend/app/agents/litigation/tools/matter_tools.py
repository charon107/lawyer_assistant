"""Matter tools — read litigation matters and their event timelines."""

from pydantic_ai import RunContext

from app.agents.litigation.deps import LitigationDeps
from app.repositories import litigation_matter_event_repo, litigation_matter_repo


def read_matter(ctx: RunContext[LitigationDeps]) -> str:
    """读取当前案件详情。

    优先使用 ctx.deps.matter_id；如果没有，返回提示要求用户提供案件编号。

    Returns:
        JSON 格式的案件详情。
    """
    matter_id = ctx.deps.matter_id
    if not matter_id:
        return "## 未指定案件\n\n请提供案件编号（case_number）或案件 ID。"

    matter = litigation_matter_repo.get_by_id(ctx.deps.db, matter_id)
    if matter is None:
        return f"## 案件不存在\n\n案件 ID `{matter_id}` 未找到。"
    if matter.user_id != ctx.deps.user_id:
        return f"## 无权访问\n\n案件 ID `{matter_id}` 不属于当前用户。"

    return f"""## 案件详情

- **案件名称：** {matter.case_name or "—"}
- **案号：** {matter.case_number or "—"}
- **管辖法院：** {matter.court or "—"}
- **案由：** {matter.cause_of_action or "—"}
- **案件类型：** {matter.case_type or "—"}
- **管辖地：** {matter.jurisdiction or "—"}
- **当事人地位：** {matter.our_side or "—"}
- **对方当事人：** {matter.counterparty or "—"}
- **状态：** {matter.status}
- **审理阶段：** {matter.stage or "—"}
- **风险评级：** {matter.risk or "—"}
- **重大性：** {matter.materiality or "—"}
- **敞口范围：** {matter.exposure_range or "—"}
- **立案日期：** {matter.filing_date.isoformat() if matter.filing_date else "—"}
- **下一期限：** {matter.next_deadline.isoformat() if matter.next_deadline else "—"}
- **初始案件理论：** {matter.initial_theory or "—"}
- **备注：** {matter.notes or "—"}
- **来源：** {matter.source}
"""


def read_matter_events(ctx: RunContext[LitigationDeps]) -> str:
    """读取案件时间线（所有事件，按时间倒序）。

    需要 ctx.deps.matter_id 已设置。

    Returns:
        Markdown 表格格式的事件时间线。
    """
    matter_id = ctx.deps.matter_id
    if not matter_id:
        return "## 未指定案件\n\n请先调用 `read_matter` 设置 matter_id。"

    events = litigation_matter_event_repo.list_by_matter(
        ctx.deps.db, matter_id=matter_id, limit=200
    )
    if not events:
        return "## 暂无事件记录\n\n该案件尚无事件时间线。"

    lines = ["## 案件时间线", ""]
    lines.append("| 日期 | 类型 | 摘要 | 期限状态 |")
    lines.append("|------|------|------|----------|")
    for ev in events:
        date_str = ev.event_date.isoformat() if ev.event_date else "—"
        deadline_str = ev.deadline_status or "—"
        summary = (ev.summary or "")[:80]
        lines.append(f"| {date_str} | {ev.event_type} | {summary} | {deadline_str} |")
    lines.append("")
    lines.append(f"共 {len(events)} 条事件。")
    return "\n".join(lines)
