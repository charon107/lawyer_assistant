"""Tools for the escalation-flagger skill + deviation sink.

- `read_escalation_matrix` lets the escalation-flagger read the user's
  configured approval matrix (who signs off on which severity of
  deviation), so the model maps a review's worst deviation to the right
  approver instead of guessing.
- `write_contract_deviation` persists a single clause-level deviation to
  `contract_deviations`. This is the data line that feeds the Phase C
  playbook-monitor ("≥5 deviations on one clause in 12 months → propose a
  playbook update"). It uses `deps.review_id` so deviations are always
  tied to the review currently being run.
"""

import json

from pydantic_ai import RunContext

from app.agents.commercial.deps import CommercialDeps
from app.repositories import (
    commercial_profile_repo,
    contract_deviation_repo,
    contract_review_repo,
)

Severity = str  # one of green / yellow / orange / red, validated by the model prompt


async def read_escalation_matrix(ctx: RunContext[CommercialDeps]) -> str:
    """读取用户配置的「上报矩阵」(escalation matrix)，决定谁来批。

    上报矩阵定义：什么严重度的偏差，需要谁（GC / CFO / 采购负责人……）
    通过什么渠道（邮件 / Slack / 飞书 / 会议）批准。escalation-flagger
    技能据此把一份审查里最严重的偏差映射到正确的审批人，而不是凭空猜。

    Returns:
        上报矩阵的 JSON 字符串；若未配置则返回提示文本。
    """
    deps = ctx.deps
    profile = commercial_profile_repo.get_by_user_id(deps.db, deps.user_id)
    if profile is None:
        return "用户尚未完成实践画像配置，没有上报矩阵。请提醒用户先完成冷启动配置。"
    if not profile.escalation_matrix:
        return (
            "用户尚未配置上报矩阵（escalation matrix）。"
            "无法据此确定审批人；请基于偏差严重度给出建议审批人，并标注为待用户确认。"
        )
    # Stored as JSON text; hand it back verbatim for the model to read.
    return profile.escalation_matrix


async def write_contract_deviation(
    ctx: RunContext[CommercialDeps],
    clause_key: str,
    clause_label: str | None = None,
    playbook_position: str | None = None,
    signed_position: str | None = None,
    severity_legal: Severity = "green",
    severity_commercial: Severity = "green",
    category: str | None = None,
) -> str:
    """把**单条**合同偏差落库到 contract_deviations。

    这是喂给 Phase C「手册监控」(playbook-monitor) 的数据线：同一条款
    在 12 个月内被偏离 ≥5 次时，系统会提议更新手册。每发现一条值得沉淀
    的偏差就调用一次本工具（红线短路场景也应至少落一条）。

    Args:
        clause_key: 条款族的稳定机器标识（如 liability_cap），与手册一致。
        clause_label: 人类可读的条款名（如「责任上限」）。
        playbook_position: 手册里的标准 / 底线立场。
        signed_position: 合同实际签署的立场（逐字引用合同原文）。
        severity_legal: 法律风险轴颜色 — green / yellow / orange / red。
        severity_commercial: 商业摩擦轴颜色 — green / yellow / orange / red。
        category: 可选分类（如 liability / data / ip / term）。

    Returns:
        JSON 字符串，含被持久化的 deviation_id。
    """
    deps = ctx.deps
    if deps.review_id is None:
        raise RuntimeError(
            "CommercialDeps.review_id is None — the WS handler must "
            "pre-create the ContractReview row before logging deviations."
        )

    review = contract_review_repo.get_by_id(deps.db, deps.review_id)
    if review is None or review.user_id != deps.user_id:
        raise PermissionError(
            f"Cannot log a deviation against review {deps.review_id} (not found, or wrong user)."
        )

    deviation = contract_deviation_repo.create(
        deps.db,
        user_id=deps.user_id,
        review_id=deps.review_id,
        clause_key=clause_key,
        clause_label=clause_label,
        playbook_position=playbook_position,
        signed_position=signed_position,
        severity_legal=severity_legal,
        severity_commercial=severity_commercial,
        category=category,
    )

    return json.dumps({"deviation_id": deviation.id}, ensure_ascii=False)
