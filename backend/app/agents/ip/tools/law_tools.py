"""IP law-research tool: registration scope from the practice profile.

Returns the profile's IP scope + registration jurisdictions for context. For
primary-source law text the skill uses the separately-attached `search_law` /
`get_law_article` tools and tags `[法条原文]` (商标法 / 专利法 / 著作权法 /
反不正当竞争法 及司法解释).
"""

import json

from pydantic_ai import RunContext

from app.agents.ip.deps import IpDeps
from app.agents.ip.tools.profile_tools import _loads
from app.repositories import ip_profile_repo


async def research_ip_rules(ctx: RunContext[IpDeps], topic: str, regime: str = "") -> str:
    """检索知识产权某主题（如混淆可能性、全面覆盖/等同、合理使用、合理使用四因素、续展期限、商业秘密三要件）下的规则。

    先返回实践画像的 IP 业务领域组合与注册管辖域作为上下文；法条原文请调用
    search_law/get_law_article 获取并标注 [法条原文]，不得凭记忆补充。时效关键问题必须先检索。

    Args:
        topic: 主题关键词，例如 "混淆可能性"、"等同侵权"、"合理使用"、"商业秘密保密措施"。
        regime: 适用法律，例如 "商标法"、"专利法"、"著作权法"、"反不正当竞争法"、"信息网络传播权保护条例"。

    Returns:
        JSON 字符串。
    """
    profile = ip_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    return json.dumps(
        {
            "topic": topic,
            "regime": regime,
            "ip_scope": _loads(profile.ip_scope) if profile else None,
            "registration_jurisdictions": (
                _loads(profile.registration_jurisdictions) if profile else None
            ),
            "note": (
                "以上为实践画像中的 IP 业务领域与注册管辖域。法条原文请调用 "
                "search_law/get_law_article 获取并标注 [法条原文]；检索零/极少结果时报告并停止，"
                "不得凭记忆补充。涉港澳台/境外时识别并适用对应法域，绝不用错误管辖域法律给自信答案。"
            ),
        },
        ensure_ascii=False,
    )
