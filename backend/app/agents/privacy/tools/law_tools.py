"""Privacy law-research tool: regulatory footprint from the practice profile.

Returns the profile's regulatory footprint for context. For primary-source
law text the skill uses the separately-attached `search_law` /
`get_law_article` tools and tags `[法条原文]` (个保法 / 数安法 / 网安法 及配套).
"""

import json

from pydantic_ai import RunContext

from app.agents.privacy.deps import PrivacyDeps
from app.agents.privacy.tools.profile_tools import _loads
from app.repositories import privacy_profile_repo


async def research_privacy_rules(ctx: RunContext[PrivacyDeps], topic: str, regime: str = "") -> str:
    """检索个人信息保护某主题（如法定评估触发、数据出境机制、敏感个人信息、泄露通知时限、主体权利期限）下的规则。

    先返回实践画像的监管覆盖范围作为上下文；法条原文请调用 search_law/get_law_article
    获取并标注 [法条原文]，不得凭记忆补充。时效关键问题必须先检索。

    Args:
        topic: 主题关键词，例如 "数据出境"、"敏感个人信息"、"泄露通知"、"删除权"。
        regime: 适用制度，例如 "个保法"、"数据安全法"、"网络安全法"、"儿童个人信息网络保护规定"。

    Returns:
        JSON 字符串。
    """
    profile = privacy_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    footprint = _loads(profile.regulatory_footprint) if profile else None
    return json.dumps(
        {
            "topic": topic,
            "regime": regime,
            "regulatory_footprint": footprint,
            "note": (
                "以上为实践画像中的监管覆盖范围。法条原文请调用 search_law/get_law_article "
                "获取并标注 [法条原文]；检索零/极少结果时报告并停止，不得凭记忆补充。"
            ),
        },
        ensure_ascii=False,
    )
