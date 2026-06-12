"""Litigation law-research tool: jurisdiction context from the practice profile.

Mirrors ip-legal's ``research_ip_rules``: returns the user's dispute_profile
(常见管辖法院/地域) so the model frames retrieval correctly. It does NOT call
``search_law`` itself — the primary-source tools ``search_law`` /
``get_law_article`` are attached separately by the Agent factory
(``_LAW_TOOL_SKILLS``) and invoked by the model, tagged ``[法条原文]``.
"""

import json

from pydantic_ai import RunContext

from app.agents.litigation.deps import LitigationDeps
from app.repositories import litigation_profile_repo


async def research_litigation_rules(ctx: RunContext[LitigationDeps], topic: str) -> str:
    """检索争议解决某主题（如证据保全、诉讼时效中断、举证期限、调查令异议、审限）的规则上下文。

    先返回实践画像的争议画像（常见管辖法院/地域）作为上下文；法条原文请调用
    search_law/get_law_article 获取并标注 [法条原文]，零结果时报告并停止，不得凭记忆补充。
    时效/地方司法口径关键问题必须先检索。

    Args:
        topic: 检索主题，例如 "证据保全 民诉法§81"、"诉讼时效中断"、"管辖权异议期限"。

    Returns:
        JSON 字符串（画像上下文 + 检索提示）。
    """
    profile = litigation_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    dispute_profile = None
    if profile and profile.dispute_profile:
        try:
            dispute_profile = (
                json.loads(profile.dispute_profile)
                if isinstance(profile.dispute_profile, str)
                else profile.dispute_profile
            )
        except (json.JSONDecodeError, TypeError):
            dispute_profile = None

    return json.dumps(
        {
            "topic": topic,
            "dispute_profile": dispute_profile,
            "note": (
                "以上为实践画像中的争议画像（常见管辖法院/地域）。法条原文请调用 "
                "search_law/get_law_article 获取并标注 [法条原文]；检索零/极少结果时报告并停止，"
                "不得凭记忆补充。地方司法口径差异大，涉地方性规定时标注 [联网检索—需复核]。"
            ),
        },
        ensure_ascii=False,
    )
