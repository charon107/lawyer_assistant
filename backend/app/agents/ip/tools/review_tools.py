"""Review read/write tools for the ip-legal agent.

``save_review`` writes the unified ``ip_reviews`` table; if the WS handler
pre-created a row (``ctx.deps.review_id``) it updates that row, otherwise it
creates a fresh one. ``read_prior_reviews`` supports the cross-skill severity
floor + same-subject prior-context lookup.
"""

import json
from typing import Any

from pydantic_ai import RunContext

from app.agents.ip.deps import IpDeps
from app.agents.ip.tools._validators import (
    check_classification,
    check_ip_category,
    check_review_status,
    check_severity,
)
from app.repositories import ip_review_repo


def _dump(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


async def read_prior_reviews(ctx: RunContext[IpDeps], subject: str) -> str:
    """查同一标的（商标名/产品/对方当事人）的先前分析产出，用于继承跨技能严重性底线。

    Args:
        subject: 商标名 / 产品 / 发明名 / 对方当事人。

    Returns:
        JSON 字符串（list；空表示无先前记录）。
    """
    rows = ip_review_repo.list_by_subject(ctx.deps.db, user_id=ctx.deps.user_id, subject=subject)
    items = [
        {
            "id": r.id,
            "review_type": r.review_type,
            "ip_category": r.ip_category,
            "classification": r.classification,
            "severity": r.severity,
            "summary": r.result_summary,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return json.dumps(items, ensure_ascii=False)


async def save_review(
    ctx: RunContext[IpDeps],
    result_summary: str,
    result_memo: str | None = None,
    result_json: dict[str, Any] | None = None,
    subject: str | None = None,
    counterparty: str | None = None,
    ip_category: str | None = None,
    classification: str | None = None,
    severity: str | None = None,
    status: str = "final",
) -> str:
    """把一次分析的结论写回 ip_reviews（clearance/fto/invention/infringement/ip_clause/oss 完成时调用）。

    Args:
        result_summary: 一句话底线结论。
        result_memo: 完整备忘录（Markdown，含工作成果抬头）。
        result_json: 结构化结果（factors/claim_mapping/obligations/redlines/open_questions 等）。
        subject: 商标名 / 产品 / 发明名 / 对方当事人 / 合同名（用于先前上下文检索）。
        counterparty: 对方当事人（infringement/ip_clause）。
        ip_category: 仅 infringement：trademark/copyright/patent/trade_secret/design。
        classification: clearance/oss=GREEN/YELLOW/RED；invention=PURSUE/INVESTIGATE/REJECT；
            infringement=IGNORE/COMMUNICATE/CEASE_DESIST/LITIGATE。
        severity: blocking/high/medium/low（跨技能严重性底线）。
        status: draft/final。

    Returns:
        JSON 字符串，含 review_id。
    """
    review_type = ctx.deps.review_type or "clearance"
    fields: dict[str, Any] = {
        "subject": subject,
        "counterparty": counterparty,
        "ip_category": check_ip_category(ip_category),
        "classification": check_classification(classification),
        "severity": check_severity(severity),
        "result_summary": result_summary,
        "result_memo": result_memo,
        "result_json": _dump(result_json),
        "status": check_review_status(status) or "final",
    }

    if ctx.deps.review_id:
        existing = ip_review_repo.get_by_id(ctx.deps.db, ctx.deps.review_id)
        if existing is not None and existing.user_id == ctx.deps.user_id:
            ip_review_repo.update(ctx.deps.db, review=existing, **fields)
            return json.dumps({"review_id": existing.id, "status": status}, ensure_ascii=False)

    review = ip_review_repo.create(
        ctx.deps.db, user_id=ctx.deps.user_id, review_type=review_type, **fields
    )
    return json.dumps({"review_id": review.id, "status": status}, ensure_ascii=False)
