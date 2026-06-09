"""Review read/write tools for the privacy-legal agent.

``save_review`` writes the unified ``privacy_reviews`` table; if the WS
handler pre-created a row (``ctx.deps.review_id``) it updates that row,
otherwise it creates a fresh one. ``read_prior_reviews`` supports the
cross-skill severity floor + same-subject prior-context lookup.
"""

import json
from typing import Any

from pydantic_ai import RunContext

from app.agents.privacy.deps import PrivacyDeps
from app.agents.privacy.tools._validators import (
    check_classification,
    check_direction,
    check_recommendation,
    check_review_status,
    check_severity,
)
from app.repositories import privacy_review_repo


def _dump(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


async def read_prior_reviews(ctx: RunContext[PrivacyDeps], subject: str) -> str:
    """查同一处理活动/对方当事人的先前分析产出（分诊/PIA/DPA），用于继承跨技能严重性底线。

    Args:
        subject: 处理活动名 / 对方当事人 / 法规名。

    Returns:
        JSON 字符串（list；空表示无先前记录）。
    """
    rows = privacy_review_repo.list_by_subject(
        ctx.deps.db, user_id=ctx.deps.user_id, subject=subject
    )
    items = [
        {
            "id": r.id,
            "review_type": r.review_type,
            "classification": r.classification,
            "severity": r.severity,
            "recommendation": r.recommendation,
            "summary": r.result_summary,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return json.dumps(items, ensure_ascii=False)


async def save_review(
    ctx: RunContext[PrivacyDeps],
    result_summary: str,
    result_memo: str | None = None,
    result_json: dict[str, Any] | None = None,
    subject: str | None = None,
    counterparty: str | None = None,
    direction: str | None = None,
    classification: str | None = None,
    severity: str | None = None,
    recommendation: str | None = None,
    status: str = "final",
) -> str:
    """把一次分析的结论写回 privacy_reviews（triage/pia/dpa/gap/policy_sweep 完成时调用）。

    Args:
        result_summary: 一句话底线结论。
        result_memo: 完整备忘录（Markdown）。
        result_json: 结构化结果（conditions/redlines/risks/remediation/required 等）。
        subject: 处理活动名 / 对方当事人 / 法规名（用于先前上下文检索）。
        counterparty: 对方当事人（DPA/PIA）。
        direction: 仅 DPA：entrusted（受托处理者）/ handler（处理者）。
        classification: 仅分诊：PROCEED/PIA_REQUIRED/DPIA_MANDATORY/STOP。
        severity: blocking/high/medium/low（跨技能严重性底线）。
        recommendation: 仅 PIA：APPROVED/WITH_CONDITIONS/CHANGES_REQUIRED/NOT_APPROVED。
        status: draft/final。

    Returns:
        JSON 字符串，含 review_id。
    """
    review_type = ctx.deps.review_type or "triage"
    fields: dict[str, Any] = {
        "subject": subject,
        "counterparty": counterparty,
        "direction": check_direction(direction),
        "classification": check_classification(classification),
        "severity": check_severity(severity),
        "recommendation": check_recommendation(recommendation),
        "result_summary": result_summary,
        "result_memo": result_memo,
        "result_json": _dump(result_json),
        "status": check_review_status(status) or "final",
    }

    if ctx.deps.review_id:
        existing = privacy_review_repo.get_by_id(ctx.deps.db, ctx.deps.review_id)
        if existing is not None and existing.user_id == ctx.deps.user_id:
            privacy_review_repo.update(ctx.deps.db, review=existing, **fields)
            return json.dumps({"review_id": existing.id, "status": status}, ensure_ascii=False)

    review = privacy_review_repo.create(
        ctx.deps.db, user_id=ctx.deps.user_id, review_type=review_type, **fields
    )
    return json.dumps({"review_id": review.id, "status": status}, ensure_ascii=False)
