"""Review-result write tool for the employment-legal agent."""

import json

from pydantic_ai import RunContext

from app.agents.employment.deps import EmploymentDeps
from app.repositories import employment_review_repo


async def save_review_result(
    ctx: RunContext[EmploymentDeps],
    result_status: str,
    result_summary: str,
    result_memo: str | None = None,
    high_risk_flags: list[str] | None = None,
    employee_name: str | None = None,
    position: str | None = None,
    jurisdiction: str | None = None,
    required_approver: str | None = None,
) -> str:
    """把一次审查的结论写回数据库（hiring/termination/classification/handbook 完成时调用）。

    Args:
        result_status: proceed / needs_fix / stop / in_progress。
        result_summary: 一句话底线结论。
        result_memo: 完整审查备忘录（Markdown）。
        high_risk_flags: 触发的高风险标记 id 列表。
        employee_name / position / jurisdiction: 审查对象信息。
        required_approver: 若需上报，填上报对象。

    Returns:
        JSON 字符串，含 review_id。
    """
    flags_json = json.dumps(high_risk_flags, ensure_ascii=False) if high_risk_flags else None
    review = employment_review_repo.create(
        ctx.deps.db,
        user_id=ctx.deps.user_id,
        review_type=ctx.deps.review_type or "hiring",
        result_status=result_status,
        result_summary=result_summary,
        result_memo=result_memo,
        high_risk_flags=flags_json,
        employee_name=employee_name,
        position=position,
        jurisdiction=jurisdiction,
        required_approver=required_approver,
        escalation_sent=bool(required_approver),
    )
    return json.dumps({"review_id": review.id, "status": result_status}, ensure_ascii=False)
