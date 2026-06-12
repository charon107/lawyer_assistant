"""Litigation-specific law tool — thin wrapper over the shared search_law.

Reads the user's dispute_profile (常见管辖法院/地域) before searching,
so results are jurisdiction-aware. Annotates results per §7.19 source labels.
"""

from pydantic_ai import RunContext

from app.agents.litigation.deps import LitigationDeps
from app.agents.tools.law_tools import search_law
from app.repositories import litigation_profile_repo


def research_litigation_rules(ctx: RunContext[LitigationDeps], topic: str) -> str:
    """检索争议解决相关法条（民诉法/民诉法解释/证据规定/民法典时效/执行规定）。

    先读取用户 dispute_profile 获取常见管辖法院和地域，再进行 RAG 检索。
    结果按 §7.19 来源标签标注（[本地知识库] / [模型知识—需验证]）。

    Args:
        topic: 检索主题，例如 "证据保全 民诉法§81"、"诉讼时效中断"。

    Returns:
        Markdown 格式的法条/司法解释/判例列表。
    """
    profile = litigation_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    jurisdiction_hint = ""
    if profile and profile.dispute_profile:
        import json

        try:
            dp = (
                json.loads(profile.dispute_profile)
                if isinstance(profile.dispute_profile, str)
                else profile.dispute_profile
            )
            courts = dp.get("common_courts", []) if isinstance(dp, dict) else []
            if courts:
                jurisdiction_hint = f"（用户常见管辖法院：{'、'.join(courts[:3])}）"
        except (json.JSONDecodeError, TypeError):
            pass

    results = search_law(topic, top_k=5)
    if not results:
        return (
            f"## 法条检索：{topic}\n\n"
            f"未在本地知识库中找到相关结果。{jurisdiction_hint}\n\n"
            f"> [模型知识—需验证] 以下内容来自模型训练数据，未经验证。"
            f"请用户核实后使用，或提供具体法条文本。"
        )

    lines = [f"## 法条检索：{topic}", "", f"{jurisdiction_hint}", ""]
    for item in results:
        title = item.get("title", item.get("law_name", "未知法条"))
        content = item.get("content", item.get("text", ""))
        source = item.get("source", "本地知识库")
        lines.append(f"### {title} `[{source}]`")
        if content:
            lines.append(content[:800])
        lines.append("")

    return "\n".join(lines)
