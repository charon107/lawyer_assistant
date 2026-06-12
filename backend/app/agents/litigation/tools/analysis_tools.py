"""Analysis tools — read/write litigation analyses (9 types).

save_analysis is the primary write tool for WS Agent skills. The handler
pre-creates the row and sets analysis_id + analysis_type in deps.
"""

from pydantic_ai import RunContext

from app.agents.litigation.deps import LitigationDeps
from app.repositories import litigation_analysis_repo


def read_analysis(ctx: RunContext[LitigationDeps]) -> str:
    """读取当前分析记录详情。

    需要 ctx.deps.analysis_id 已设置。

    Returns:
        JSON 格式的分析详情。
    """
    analysis_id = ctx.deps.analysis_id
    if not analysis_id:
        return "## 未指定分析记录\n\n请提供 analysis_id。"

    analysis = litigation_analysis_repo.get_by_id(ctx.deps.db, analysis_id)
    if analysis is None:
        return f"## 分析记录不存在\n\nanalysis_id `{analysis_id}` 未找到。"
    if analysis.user_id != ctx.deps.user_id:
        return f"## 无权访问\n\nanalysis_id `{analysis_id}` 不属于当前用户。"

    return f"""## 分析详情

- **类型：** {analysis.analysis_type}
- **主题：** {analysis.subject or "—"}
- **相对方：** {analysis.counterparty or "—"}
- **分类：** {analysis.classification or "—"}
- **严重性：** {analysis.severity or "—"}
- **状态：** {analysis.status}

### 摘要
{analysis.result_summary or "（无）"}

### 全文
{analysis.result_memo or "（无）"}

### 结构化数据
```json
{analysis.result_json or "{}"}
```
"""


def read_prior_analyses(ctx: RunContext[LitigationDeps]) -> str:
    """读取同主题/同案件/同对手的历史分析（用于 prior-context 检索和严重性底线）。

    Returns:
        Markdown 格式的历史分析列表。
    """
    matter_id = ctx.deps.matter_id
    analysis_id = ctx.deps.analysis_id
    subject = None

    # 先尝试从当前分析获取 subject
    if analysis_id:
        analysis = litigation_analysis_repo.get_by_id(ctx.deps.db, analysis_id)
        if analysis:
            subject = analysis.subject

    results: list[str] = []

    # 按 subject 查
    if subject:
        prior = litigation_analysis_repo.list_by_subject(
            ctx.deps.db, user_id=ctx.deps.user_id, subject=subject, limit=10
        )
        # 排除当前记录
        prior = [a for a in prior if a.id != (analysis_id or "")]
        if prior:
            results.append(f"## 同主题历史分析（{subject}）\n")
            for a in prior:
                results.append(
                    f"- [{a.analysis_type}] {a.subject or '—'} "
                    f"({a.severity or '无'} / {a.classification or '—'}) "
                    f"— {a.result_summary or '无摘要'}"
                )

    # 按 matter_id 查
    if matter_id:
        matter_list, _ = litigation_analysis_repo.list_by_user(
            ctx.deps.db, user_id=ctx.deps.user_id, matter_id=matter_id, limit=20
        )
        matter_list = [a for a in matter_list if a.id != (analysis_id or "")]
        if matter_list:
            results.append("\n## 同案件历史分析\n")
            for a in matter_list:
                results.append(
                    f"- [{a.analysis_type}] {a.subject or '—'} "
                    f"({a.severity or '无'}) — {a.result_summary or '无摘要'}"
                )

    if not results:
        return "## 无历史分析记录"
    return "\n".join(results)


def save_analysis(
    ctx: RunContext[LitigationDeps],
    result_summary: str,
    result_memo: str,
    *,
    result_json: str | None = None,
    severity: str | None = None,
    classification: str | None = None,
) -> str:
    """保存分析结果到当前预建行。

    Args:
        result_summary: 底线摘要（一两句）。
        result_memo: 全文 Markdown（含工作成果抬头）。
        result_json: 结构化数据 (JSON 字符串)。
        severity: 严重性 (blocking/high/medium/low)。
        classification: 技能分类标签。

    Returns:
        确认信息。
    """
    analysis_id = ctx.deps.analysis_id
    if not analysis_id:
        return "## 错误：未预建分析行，无法保存。请联系系统管理员。"

    fields: dict = {
        "result_summary": result_summary,
        "result_memo": result_memo,
        "status": "final",
    }
    if result_json is not None:
        fields["result_json"] = result_json
    if severity is not None:
        fields["severity"] = severity
    if classification is not None:
        fields["classification"] = classification

    litigation_analysis_repo.update(
        ctx.deps.db,
        analysis=litigation_analysis_repo.get_by_id(ctx.deps.db, analysis_id),
        **fields,
    )
    return f"分析结果已保存 (analysis_id={analysis_id})。"
