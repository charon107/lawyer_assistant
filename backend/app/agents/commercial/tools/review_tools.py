"""Tools that persist the review result back to the database.

`write_contract_review` is intentionally the LAST tool the agent
calls in a vendor-review run. The agent is told to call it with the
finished memo + structured deviation list; the WS handler reads the
returned review_id and broadcasts the final state to the frontend.
"""

import json
from typing import Any, Literal

from pydantic_ai import ModelRetry, RunContext

from app.agents.commercial.deps import CommercialDeps
from app.repositories import contract_review_repo
from app.schemas.commercial.review import ContractReviewResult

ResultStatus = Literal["green", "yellow", "red"]


def _coerce_list(value: Any, field_name: str) -> list[Any]:
    """Coerce an array-shaped tool argument into a real list.

    Some OpenAI-compatible models (e.g. Xiaomi MiMo) serialize array
    arguments as JSON-encoded *strings* (``'[]'`` / ``'[{...}]'``)
    instead of native arrays. Model output is untrusted, so we coerce
    at the tool boundary rather than letting pydantic reject the call.

    - ``None`` → ``[]``
    - ``list`` → unchanged
    - ``str`` → ``json.loads``; must decode to a list
    - anything else → ``ModelRetry`` so the model can fix its call.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelRetry(
                f"参数 {field_name} 必须是数组。收到的是无法解析为 JSON 的字符串。"
            ) from exc
        if not isinstance(decoded, list):
            raise ModelRetry(
                f"参数 {field_name} 必须是数组（JSON array），收到的是 {type(decoded).__name__}。"
            )
        return decoded
    raise ModelRetry(f"参数 {field_name} 必须是数组，收到的是 {type(value).__name__}。")


async def write_contract_review(
    ctx: RunContext[CommercialDeps],
    result_status: ResultStatus,
    result_summary: str,
    result_memo: str,
    deviations: list[dict[str, Any]] | str | None = None,
    favorable_terms: list[str] | str | None = None,
    missing_terms: list[str] | str | None = None,
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

    # Coerce array args (some models pass them as JSON strings), then
    # build the structured result via Pydantic for shape validation and
    # hand it to the repo (which JSON-encodes it).
    payload = ContractReviewResult(
        summary=result_summary,
        deviations=_coerce_list(deviations, "deviations"),
        favorable_terms=_coerce_list(favorable_terms, "favorable_terms"),
        missing_terms=_coerce_list(missing_terms, "missing_terms"),
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


def _load_owned_review(deps: CommercialDeps):  # type: ignore[no-untyped-def]
    """Fetch the run's review row, enforcing presence + ownership.

    Shared by the stakeholder-summary / escalation skills, which operate on
    an already-completed review rather than creating a new one.
    """
    if deps.review_id is None:
        raise RuntimeError(
            "CommercialDeps.review_id is None — the WS handler must pass the "
            "target ContractReview id before running this skill."
        )
    review = contract_review_repo.get_by_id(deps.db, deps.review_id)
    if review is None or review.user_id != deps.user_id:
        raise PermissionError(f"Cannot access review {deps.review_id} (not found, or wrong user).")
    return review


async def read_contract_review(ctx: RunContext[CommercialDeps]) -> str:
    """读取当前审查记录的已有结论，作为后续技能的输入。

    stakeholder-summary（业务摘要）和 escalation-flagger（定审批人）都建立
    在一份**已完成的法律审查**之上。先调用本工具拿到法律审查的结论、备忘录
    和结构化偏差，再据此撰写业务摘要 / 推断审批人。

    Returns:
        JSON 字符串，含 review_type / result_status / result_summary /
        result_memo / result_json / required_approver 等字段。
    """
    review = _load_owned_review(ctx.deps)
    return json.dumps(
        {
            "review_id": review.id,
            "review_type": review.review_type,
            "counterparty": review.counterparty,
            "agreement_name": review.agreement_name,
            "result_status": review.result_status,
            "result_summary": review.result_summary,
            "result_memo": review.result_memo,
            "result_json": review.result_json,
            "required_approver": review.required_approver,
        },
        ensure_ascii=False,
    )


async def write_stakeholder_summary(
    ctx: RunContext[CommercialDeps],
    summary: str,
) -> str:
    """把面向业务方的摘要写回数据库（contract_reviews.stakeholder_summary）。

    这是 stakeholder-summary 技能的最后一步。摘要应当用**业务语言**（不是
    法言法语）讲清楚：这份合同能不能签、最关键的两三个商业影响、需要业务
    方做什么决定。

    Args:
        summary: 业务语言摘要（Markdown）。

    Returns:
        JSON 字符串，含 review_id。
    """
    deps = ctx.deps
    review = _load_owned_review(deps)
    contract_review_repo.update_result(
        deps.db,
        review=review,
        stakeholder_summary=summary,
    )
    return json.dumps({"review_id": review.id}, ensure_ascii=False)


async def write_escalation_decision(
    ctx: RunContext[CommercialDeps],
    required_approver: str,
    escalation_sent: bool = False,
) -> str:
    """把上报路由决定写回数据库（required_approver + escalation_sent）。

    这是 escalation-flagger 技能的最后一步。先用 `read_escalation_matrix`
    读上报矩阵、用 `read_contract_review` 读审查结论，据此确定**谁来批**，
    再调用本工具写回。

    Args:
        required_approver: 确定的审批人（如 "GC" / "CFO" / "采购负责人"）。
        escalation_sent: 是否已实际发出上报通知。默认 False（仅记录决定，
            不代表已通知）。

    Returns:
        JSON 字符串，含 review_id 和 required_approver。
    """
    deps = ctx.deps
    review = _load_owned_review(deps)
    contract_review_repo.update_result(
        deps.db,
        review=review,
        required_approver=required_approver,
        escalation_sent=escalation_sent,
    )
    return json.dumps(
        {"review_id": review.id, "required_approver": required_approver},
        ensure_ascii=False,
    )
