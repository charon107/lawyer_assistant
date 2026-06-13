"""Analysis tools — write regulatory analyses + hand off gaps.

save_analysis: writes the pre-created regulatory_analyses row (policy_diff /
policy_redraft). The handler seeds analysis_id + analysis_type in deps.

save_gap (review decision A3): dedup key = (regulation_citation + policy_affected);
fall back to normalized requirement text only when citation is absent. Carries
the upstream severity floor (never silently downgraded).
"""

from pydantic_ai import RunContext

from app.agents.regulatory.deps import RegulatoryDeps
from app.agents.regulatory.tools._validators import normalize_gap_type, normalize_severity
from app.repositories import regulatory_analysis_repo, regulatory_gap_repo


def save_analysis(
    ctx: RunContext[RegulatoryDeps],
    result_summary: str,
    result_memo: str,
    *,
    subject: str | None = None,
    regulation_name: str | None = None,
    policy_affected: str | None = None,
    severity: str | None = None,
    scope_limited: bool = False,
    scope_note: str | None = None,
    status_verified: bool = False,
    result_json: str | None = None,
) -> str:
    """保存分析结果到预建行（policy_diff / policy_redraft）。

    Args:
        result_summary: 底线摘要。
        result_memo: 全文 Markdown（含工作成果抬头）。
        scope_limited: policy-diff 范围限制标记（大声且永久）。
        status_verified: 法规状态是否已核实（否则输出加横幅）。

    Returns:
        确认信息。
    """
    analysis_id = ctx.deps.analysis_id
    if not analysis_id:
        return "## 错误：未预建分析行，无法保存。"

    fields: dict = {
        "result_summary": result_summary,
        "result_memo": result_memo,
        "scope_limited": scope_limited,
        "status_verified": status_verified,
        "status": "final",
    }
    if subject is not None:
        fields["subject"] = subject
    if regulation_name is not None:
        fields["regulation_name"] = regulation_name
    if policy_affected is not None:
        fields["policy_affected"] = policy_affected
    if scope_note is not None:
        fields["scope_note"] = scope_note
    if result_json is not None:
        fields["result_json"] = result_json
    sev = normalize_severity(severity)
    if sev is not None:
        fields["severity"] = sev

    analysis = regulatory_analysis_repo.get_by_id(ctx.deps.db, analysis_id)
    if analysis is None or analysis.user_id != ctx.deps.user_id:
        return "## 错误：分析行不存在或无权访问。"
    regulatory_analysis_repo.update(ctx.deps.db, analysis=analysis, **fields)
    return f"分析结果已保存 (analysis_id={analysis_id})。"


def save_gap(
    ctx: RunContext[RegulatoryDeps],
    requirement: str,
    policy_affected: str,
    *,
    regulation: str | None = None,
    regulation_citation: str | None = None,
    gap_type: str | None = None,
    severity: str | None = None,
    owner: str | None = None,
    due: str | None = None,
    status_verified: bool = False,
) -> str:
    """policy-diff 交接：去重后追加 regulatory_gaps（A3 引用去重 + 严重性底线）。

    Args:
        requirement: 法规要求内容。
        policy_affected: 受影响政策名 或 "需要制定新政策"。
        regulation_citation: 法条引用（A3 稳定去重键）。
        due: 截止日期 YYYY-MM-DD（可空）。

    Returns:
        确认或去重提示。
    """
    from datetime import date

    requirement_norm = (requirement or "").strip()
    dup = regulatory_gap_repo.find_duplicate(
        ctx.deps.db,
        user_id=ctx.deps.user_id,
        policy_affected=policy_affected,
        regulation_citation=regulation_citation,
        requirement_normalized=requirement_norm if not regulation_citation else None,
    )
    if dup is not None:
        return (
            f"已存在同一差距（id={dup.id}，引用={dup.regulation_citation or '—'}，"
            f"政策={policy_affected}），未重复创建。"
        )

    due_date = None
    if due:
        try:
            due_date = date.fromisoformat(due.strip())
        except (ValueError, AttributeError):
            due_date = None

    gap = regulatory_gap_repo.create(
        ctx.deps.db,
        user_id=ctx.deps.user_id,
        reg_item_id=ctx.deps.reg_item_id,
        analysis_id=ctx.deps.analysis_id,
        requirement=requirement_norm,
        regulation=regulation,
        regulation_citation=regulation_citation,
        policy_affected=policy_affected,
        gap_type=normalize_gap_type(gap_type),
        severity=normalize_severity(severity),
        owner=owner,
        opened=date.today(),
        due=due_date,
        status_verified=status_verified,
        status="open",
    )
    return f"差距已加入追踪器（id={gap.id}，类型={gap.gap_type}，严重性={gap.severity or '—'}）。"
