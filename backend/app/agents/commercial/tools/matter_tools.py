"""Tool that reads the background of a tracked matter.

A "matter" (`commercial_matters`) groups one counterparty relationship.
Review / summary skills call `read_matter_context` to pull the matter's
counterparty, agreement type, status, owner, and free-text notes so the
report is grounded in the existing relationship rather than treating each
contract as a cold start.

Read-only. Ownership is enforced: a user can only read their own matters.
"""

from pydantic_ai import RunContext

from app.agents.commercial.deps import CommercialDeps
from app.repositories import commercial_matter_repo


async def read_matter_context(
    ctx: RunContext[CommercialDeps],
    matter_id: str,
) -> str:
    """读取关联事项（matter）的背景信息，作为审查 / 摘要的上下文。

    一个「事项」聚合一段对方关系：对手方、协议类型、状态、负责人、备注。
    在审查或撰写摘要前调用本工具，可以把报告锚定到既有关系上，而不是把
    每份合同都当成全新关系处理。

    Args:
        matter_id: 事项 ID。

    Returns:
        Markdown 背景卡；若事项不存在或不属于当前用户，返回提示文本
        （不抛异常，让模型据此决定是否继续）。
    """
    deps = ctx.deps
    matter = commercial_matter_repo.get_by_id(deps.db, matter_id)
    if matter is None or matter.user_id != deps.user_id:
        return f"未找到事项 {matter_id}（不存在或不属于当前用户）。请在不依赖事项背景的前提下继续审查。"

    lines = ["## 关联事项背景", ""]
    lines.append(f"- 事项 ID：{matter.id}")
    if matter.matter_name:
        lines.append(f"- 名称：{matter.matter_name}")
    if matter.counterparty:
        lines.append(f"- 对手方：{matter.counterparty}")
    if matter.agreement_type:
        lines.append(f"- 协议类型：{matter.agreement_type}")
    lines.append(f"- 状态：{matter.status}")
    if matter.owner:
        lines.append(f"- 负责人：{matter.owner}")
    if matter.notes:
        lines.append("")
        lines.append("### 备注")
        lines.append(matter.notes.strip())

    return "\n".join(lines)
