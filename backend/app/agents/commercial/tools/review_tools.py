"""Tools that persist the review result back to the database.

`write_contract_review` is intentionally the LAST tool the agent
calls in a vendor-review run. The agent is told to call it with the
finished memo + structured deviation list; the WS handler reads the
returned review_id and broadcasts the final state to the frontend.
"""

import json
from typing import Any, Literal

from pydantic_ai import RunContext

from app.agents.commercial.deps import CommercialDeps
from app.repositories import contract_review_repo
from app.schemas.commercial.review import ContractReviewResult

ResultStatus = Literal["green", "yellow", "red"]


async def write_contract_review(
    ctx: RunContext[CommercialDeps],
    result_status: ResultStatus,
    result_summary: str,
    result_memo: str,
    deviations: list[dict[str, Any]] | None = None,
    favorable_terms: list[str] | None = None,
    missing_terms: list[str] | None = None,
    required_approver: str | None = None,
) -> str:
    """把审查结论写回数据库。

    这是 vendor-agreement-review 流程的最后一步。**没有调用本工具的
    运行被视为未完成**。调用一次后即可结束本轮对话。

    Args:
        result_status: 总体结论 — green / yellow / red
            （任一红 → red；任一橙 → yellow；其余 → green）。
        result_summary: 2 句话底线（一句结论 + 一句最关键风险）。
        result_memo: 完整 Markdown 备忘录。
        deviations: 偏差列表，每条按 DeviationItem 结构。
        favorable_terms: 合同里对我方有利的条款（数组）。
        missing_terms: 缺失但应当存在的条款（数组）。
        required_approver: 触达谁可以拍板。如果无需上报留空。

    Returns:
        被持久化的 review_id。
    """
    deps = ctx.deps
    if deps.review_id is None:
        raise RuntimeError(
            "CommercialDeps.review_id is None — the WS handler must "
            "pre-create the ContractReview row before kicking off the agent."
        )

    review = contract_review_repo.get_by_id(deps.db, deps.review_id)
    if review is None or review.user_id != deps.user_id:
        # Defensive: never let the agent overwrite a stranger's review.
        raise PermissionError(
            f"Cannot write to review {deps.review_id} (not found, or wrong user)."
        )

    # Build the structured result via Pydantic for shape validation, then
    # hand it to the repo (which JSON-encodes it).
    payload = ContractReviewResult(
        summary=result_summary,
        deviations=deviations or [],  # type: ignore[arg-type]
        favorable_terms=favorable_terms or [],
        missing_terms=missing_terms or [],
        required_approver=required_approver,
    )

    contract_review_repo.update_result(
        deps.db,
        review=review,
        result_status=result_status,
        result_summary=result_summary,
        result_memo=result_memo,
        result_json=payload,
        required_approver=required_approver,
    )

    return json.dumps({"review_id": review.id, "result_status": result_status})
