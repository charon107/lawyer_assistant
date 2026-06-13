"""Regulatory law-research tool: 中国行政法主题上下文 from the practice profile.

Mirrors litigation's ``research_litigation_rules``: returns the user's watchlist
context so the model frames retrieval correctly. It does NOT call ``search_law``
itself — the primary-source tools ``search_law`` / ``get_law_article`` are
attached separately by the Agent factory (``_LAW_TOOL_SKILLS``) and invoked by
the model, tagged ``[法条原文]``.
"""

import json

from pydantic_ai import RunContext

from app.agents.regulatory.deps import RegulatoryDeps
from app.repositories import regulatory_profile_repo


async def research_admin_rules(ctx: RunContext[RegulatoryDeps], topic: str) -> str:
    """检索中国行政法某主题的规则上下文（行政处罚法/复议法/诉讼法/许可法/强制法/信息公开条例/赔偿法/行政协议司法解释）。

    先返回实践画像的监测清单作为上下文；法条原文请调用 search_law/get_law_article
    获取并标注 [法条原文]，零结果时报告并停止，不得凭记忆补充。引用部门规章/行政
    规范性文件前必先检索确认现行有效（《规章制定程序条例》立法进程节点）。

    Args:
        topic: 检索主题，例如 "行政处罚 一事不再罚 行政处罚法§29"、"行政复议前置"、"政府信息公开 豁免"。

    Returns:
        JSON 字符串（画像上下文 + 检索提示）。
    """
    profile = regulatory_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    watchlist = None
    if profile and profile.watchlist:
        try:
            watchlist = (
                json.loads(profile.watchlist)
                if isinstance(profile.watchlist, str)
                else profile.watchlist
            )
        except (json.JSONDecodeError, TypeError):
            watchlist = None

    return json.dumps(
        {
            "topic": topic,
            "watchlist": watchlist,
            "note": (
                "以上为实践画像中的监测清单（关注的监管机构）。法条原文请调用 "
                "search_law/get_law_article 获取并标注 [法条原文]；检索零/极少结果时报告并停止，"
                "不得凭记忆补充。引用部门规章/行政规范性文件前必先检索确认现行有效，"
                "无法核实时标注 [模型知识—需验证]。"
            ),
        },
        ensure_ascii=False,
    )
