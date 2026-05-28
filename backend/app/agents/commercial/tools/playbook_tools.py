"""Tool exposing the user's playbook to the agent.

The playbook is the source of truth for every clause comparison the
vendor-review skill performs. It lives on
`commercial_profiles.playbook_sales` and `commercial_profiles.playbook_purchasing`
as JSON text — this tool deserializes it and returns a compact JSON
string the LLM can parse and quote from.
"""

import json
from typing import Literal

from pydantic_ai import RunContext

from app.agents.commercial.deps import CommercialDeps
from app.repositories import commercial_profile_repo


async def get_playbook(
    ctx: RunContext[CommercialDeps],
    side: Literal["sales", "purchasing"],
) -> str:
    """读取用户合同手册（指定一侧）。

    手册包含每一类条款的标准立场、底线立场和绝不接受的红线。
    使用本工具时务必明确指定 side，因为同一公司在销售侧和采购侧
    的立场通常完全不同。

    Args:
        side: "sales" 或 "purchasing"。

    Returns:
        JSON 字符串，结构是 {"side": ..., "entries": [...]}。
        如果用户未配置该侧手册，返回提示字符串。
    """
    profile = commercial_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None:
        return "⚠️ 用户尚未创建实践画像。请先引导其完成冷启动。"

    raw = profile.playbook_sales if side == "sales" else profile.playbook_purchasing
    if not raw:
        return (
            f"⚠️ 用户在「{side}」侧没有配置手册。无法逐条对比。"
            "请告知用户前往设置页面补充该侧手册，或暂时改用经验法则审查。"
        )

    # `raw` is JSON text. Re-emit pretty so the LLM gets exactly what
    # it would see in the user-facing config UI.
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        return raw  # already a plain string somehow; pass through
