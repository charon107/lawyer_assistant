"""Enforcement-letter read/write tools for the ip-legal agent.

``cease_desist`` / ``takedown`` skills read the intake record then write the
drafted letter (internal draft keeps the work-product header; the outbound
version drops it), the send-gate result, due-diligence, recommended action,
status, and audit log.
"""

import json
from typing import Any

from pydantic_ai import RunContext

from app.agents.ip.deps import IpDeps
from app.agents.ip.tools._validators import check_enforcement_status
from app.agents.ip.tools.profile_tools import _loads
from app.repositories import ip_enforcement_repo


def _dump(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


async def read_enforcement(ctx: RunContext[IpDeps]) -> str:
    """读取当前维权信函档案（类型、模式、对方、涉案权利、被诉事实、回复期限、状态）。

    Returns:
        JSON 字符串。
    """
    if not ctx.deps.enforcement_id:
        return json.dumps({"error": "未指定维权信函档案。"}, ensure_ascii=False)
    row = ip_enforcement_repo.get_by_id(ctx.deps.db, ctx.deps.enforcement_id)
    if row is None or row.user_id != ctx.deps.user_id:
        return json.dumps({"error": "维权信函档案不存在或无权访问。"}, ensure_ascii=False)
    return json.dumps(
        {
            "id": row.id,
            "matter_type": row.matter_type,
            "mode": row.mode,
            "counterparty": row.counterparty,
            "right_at_issue": _loads(row.right_at_issue),
            "infringement_facts": row.infringement_facts,
            "due_diligence": _loads(row.due_diligence),
            "response_deadline": (
                row.response_deadline.isoformat() if row.response_deadline else None
            ),
            "status": row.status,
        },
        ensure_ascii=False,
    )


async def save_letter(
    ctx: RunContext[IpDeps],
    letter_draft: str | None = None,
    outbound_letter: str | None = None,
    due_diligence: dict[str, Any] | None = None,
    send_gate: dict[str, Any] | None = None,
    recommended_action: str | None = None,
    status: str | None = None,
    log: list[dict[str, Any]] | None = None,
    escalation_flag: bool | None = None,
    escalation_reason: str | None = None,
) -> str:
    """把维权信函草稿、对外版本、对方尽调、发送门禁、建议动作、状态和审计日志写回数据库。

    Args:
        letter_draft: 内部草稿（Markdown，**带工作成果抬头**）。
        outbound_letter: 对外版本（Markdown，**去抬头**——发送给对方/平台的版本）。
        due_diligence: 对方尽调（实体/资源/IP组合/诉讼史/是否聘律/反诉风险）。
        send_gate: 发送门禁核对（权利有效/主张成立/比例适当/授权人签署/尽调已呈现）。
        recommended_action: receive/respond/counter 模式的四选项树结论。
        status: intake/drafting/gated/sent/responded/escalated/closed（系统不实际发送）。
        log: 审计日志条目。
        escalation_flag / escalation_reason: 升级标记。

    Returns:
        JSON 字符串。
    """
    if not ctx.deps.enforcement_id:
        return json.dumps({"error": "未指定维权信函档案。"}, ensure_ascii=False)
    row = ip_enforcement_repo.get_by_id(ctx.deps.db, ctx.deps.enforcement_id)
    if row is None or row.user_id != ctx.deps.user_id:
        return json.dumps({"error": "维权信函档案不存在或无权访问。"}, ensure_ascii=False)

    ip_enforcement_repo.update(
        ctx.deps.db,
        enforcement=row,
        letter_draft=letter_draft,
        outbound_letter=outbound_letter,
        due_diligence=_dump(due_diligence),
        send_gate=_dump(send_gate),
        recommended_action=recommended_action,
        status=check_enforcement_status(status),
        log=_dump(log),
        escalation_flag=escalation_flag,
        escalation_reason=escalation_reason,
    )
    return json.dumps(
        {"enforcement_id": row.id, "status": status or row.status}, ensure_ascii=False
    )
