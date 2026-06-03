"""Jurisdiction-awareness tool: per-province rules from the practice profile.

Returns the profile's stored jurisdiction_table entry for a province. For
primary-source law text the skill uses the separately-attached
`search_law` / `get_law_article` tools and tags `[法条原文]`.
"""

import json

from pydantic_ai import RunContext

from app.agents.employment.deps import EmploymentDeps
from app.agents.employment.tools.profile_tools import _loads
from app.repositories import employment_profile_repo


async def research_jurisdiction_rules(
    ctx: RunContext[EmploymentDeps], jurisdiction: str, topic: str
) -> str:
    """检索某省/直辖市在某主题（如最终工资期限、加班费基数、综合工时审批、经济补偿）下的属地规则。

    先返回实践画像 jurisdiction_table 中该省的规则与自动上报项；如需法条原文，
    再调用 search_law / get_law_article 并标注 [法条原文]。

    Args:
        jurisdiction: 省/直辖市，例如 "北京"、"上海"、"广东"。
        topic: 主题关键词。

    Returns:
        JSON 字符串。
    """
    profile = employment_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    table = _loads(profile.jurisdiction_table) if profile else None
    entry = table.get(jurisdiction) if isinstance(table, dict) else None
    return json.dumps(
        {
            "jurisdiction": jurisdiction,
            "topic": topic,
            "profile_rules": entry,
            "note": (
                "以上为实践画像中的属地规则（如有）。法条原文请调用 "
                "search_law/get_law_article 获取并标注 [法条原文]；不得凭记忆补充。"
            ),
        },
        ensure_ascii=False,
    )
