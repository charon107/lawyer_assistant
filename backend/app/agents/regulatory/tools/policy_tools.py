"""Policy / reg-item read tools for policy-diff and policy-redraft."""

import json

from pydantic_ai import RunContext

from app.agents.regulatory.deps import RegulatoryDeps
from app.repositories import (
    regulatory_analysis_repo,
    regulatory_profile_repo,
    regulatory_reg_item_repo,
)


def read_policy_library(ctx: RunContext[RegulatoryDeps]) -> str:
    """读取政策库索引（policy-diff 据此映射要求→政策，gaps 据此路由负责人）。

    Returns:
        Markdown 政策库；未配置则提示。
    """
    profile = regulatory_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None or not profile.policy_library:
        return "## 政策库未配置\n\n请在设置中维护政策库索引（政策名 / 路径 / 负责人）。"
    try:
        lib = json.loads(profile.policy_library)
    except (json.JSONDecodeError, TypeError):
        return profile.policy_library
    return "## 政策库索引\n\n```json\n" + json.dumps(lib, ensure_ascii=False, indent=2) + "\n```"


def read_reg_item(ctx: RunContext[RegulatoryDeps]) -> str:
    """读取当前法规事项作为 policy-diff 输入（需 ctx.deps.reg_item_id）。

    Returns:
        Markdown 事项详情；未指定/无权则提示。
    """
    reg_item_id = ctx.deps.reg_item_id
    if not reg_item_id:
        return "## 未指定法规事项\n\n本次为粘贴法规模式，请使用用户提供的法规文本。"
    item = regulatory_reg_item_repo.get_by_id(ctx.deps.db, reg_item_id)
    if item is None:
        return f"## 法规事项不存在\n\nreg_item_id `{reg_item_id}` 未找到。"
    if item.user_id != ctx.deps.user_id:
        return f"## 无权访问\n\nreg_item_id `{reg_item_id}` 不属于当前用户。"
    return f"""## 法规事项详情

- **标题：** {item.title or "—"}
- **监管机构：** {item.regulator or "—"}
- **类型：** {item.item_type}
- **重要度：** {item.materiality}
- **来源：** {item.source_tag or "—"}
- **法规状态已验证：** {"是" if item.status_verified else "否（输出需加未验证横幅）"}
- **生效日期：** {item.effective_date or "—"}

### 摘要
{item.summary or "（无）"}
"""


def read_prior_analyses(ctx: RunContext[RegulatoryDeps]) -> str:
    """按 subject 查历史分析，支撑跨技能严重性底线。

    Returns:
        Markdown 历史分析列表。
    """
    subject = None
    if ctx.deps.analysis_id:
        cur = regulatory_analysis_repo.get_by_id(ctx.deps.db, ctx.deps.analysis_id)
        if cur:
            subject = cur.subject
    if not subject and ctx.deps.reg_item_id:
        item = regulatory_reg_item_repo.get_by_id(ctx.deps.db, ctx.deps.reg_item_id)
        if item:
            subject = item.title
    if not subject:
        return "## 无可用主题，跳过历史检索"

    prior = regulatory_analysis_repo.list_by_subject(
        ctx.deps.db, user_id=ctx.deps.user_id, subject=subject
    )
    prior = [a for a in prior if a.id != (ctx.deps.analysis_id or "")]
    if not prior:
        return f"## 无同主题历史分析（{subject}）"
    lines = [f"## 同主题历史分析（{subject}）——严重性底线参考\n"]
    for a in prior:
        lines.append(
            f"- [{a.analysis_type}] {a.subject or '—'} "
            f"(严重性 {a.severity or '无'}) — {a.result_summary or '无摘要'}"
        )
    return "\n".join(lines)
