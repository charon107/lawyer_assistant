"""DSAR read/write tools for the privacy-legal agent."""

import json
from typing import Any

from pydantic_ai import RunContext

from app.agents.privacy.deps import PrivacyDeps
from app.agents.privacy.tools._validators import check_dsar_status
from app.agents.privacy.tools.profile_tools import _loads
from app.repositories import privacy_dsar_repo


def _dump(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


async def read_dsar(ctx: RunContext[PrivacyDeps]) -> str:
    """读取当前 DSAR 档案（请求类型、收到/验证/回复日期、回复期限、身份验证状态、已定位系统、状态）。

    Returns:
        JSON 字符串。
    """
    if not ctx.deps.dsar_id:
        return json.dumps({"error": "未指定 DSAR 档案。"}, ensure_ascii=False)
    dsar = privacy_dsar_repo.get_by_id(ctx.deps.db, ctx.deps.dsar_id)
    if dsar is None or dsar.user_id != ctx.deps.user_id:
        return json.dumps({"error": "DSAR 档案不存在或无权访问。"}, ensure_ascii=False)
    return json.dumps(
        {
            "id": dsar.id,
            "request_types": _loads(dsar.request_types),
            "data_subject_ref": dsar.data_subject_ref,
            "date_received": dsar.date_received.isoformat() if dsar.date_received else None,
            "date_verified": dsar.date_verified.isoformat() if dsar.date_verified else None,
            "response_deadline": (
                dsar.response_deadline.isoformat() if dsar.response_deadline else None
            ),
            "identity_verified": dsar.identity_verified,
            "verification_method": dsar.verification_method,
            "systems_checked": _loads(dsar.systems_checked),
            "status": dsar.status,
        },
        ensure_ascii=False,
    )


async def save_dsar_letters(
    ctx: RunContext[PrivacyDeps],
    ack_letter: str | None = None,
    response_letter: str | None = None,
    exemptions: list[dict[str, Any]] | None = None,
    systems_checked: list[dict[str, Any]] | None = None,
    status: str | None = None,
    log: list[dict[str, Any]] | None = None,
    escalation_flag: bool | None = None,
    escalation_reason: str | None = None,
) -> str:
    """把 DSAR 的两份函件、豁免分析、系统定位结果、状态和审计日志写回数据库。

    Args:
        ack_letter: 确认函（Markdown，对外，无工作成果抬头）。
        response_letter: 实质回复函（Markdown，对外）。
        exemptions: 主张的豁免列表（每项含依据，标注 [提议——需律师审核]）。
        systems_checked: 逐系统定位结果。
        status: received/verifying/locating/exemption_analysis/drafted/responded/escalated。
        log: 审计日志条目。
        escalation_flag / escalation_reason: 升级标记。

    Returns:
        JSON 字符串。
    """
    if not ctx.deps.dsar_id:
        return json.dumps({"error": "未指定 DSAR 档案。"}, ensure_ascii=False)
    dsar = privacy_dsar_repo.get_by_id(ctx.deps.db, ctx.deps.dsar_id)
    if dsar is None or dsar.user_id != ctx.deps.user_id:
        return json.dumps({"error": "DSAR 档案不存在或无权访问。"}, ensure_ascii=False)

    privacy_dsar_repo.update(
        ctx.deps.db,
        dsar=dsar,
        ack_letter=ack_letter,
        response_letter=response_letter,
        exemptions=_dump(exemptions),
        systems_checked=_dump(systems_checked),
        status=check_dsar_status(status),
        log=_dump(log),
        escalation_flag=escalation_flag,
        escalation_reason=escalation_reason,
    )
    return json.dumps({"dsar_id": dsar.id, "status": status or dsar.status}, ensure_ascii=False)
