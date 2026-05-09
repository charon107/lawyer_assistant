"""Legal knowledge retrieval tools for PydanticAI agent.

Registered as @agent.tool in assistant.py.
"""

from pydantic_ai import RunContext

from app.agents.assistant import Deps
from app.services.law_search import LawSearchService


def _format_search_results(results: list, query: str) -> str:
    """Format search results as readable text for LLM consumption."""
    if not results:
        return f"未找到与「{query}」相关的法律条文。"

    lines = [f"找到 {len(results)} 条相关法律条文：\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r.citation}（相关度：{r.score:.2f}）")
        # Truncate long articles for readability
        content = r.article.content
        if len(content) > 300:
            content = content[:300] + "..."
        lines.append(f"   {content}\n")
    return "\n".join(lines)


async def search_law(
    ctx: RunContext[Deps],
    query: str,
    category: str | None = None,
    source_type: str | None = None,
    top_k: int = 5,
) -> str:
    """搜索中国法律条文。当需要查找法律依据、法条引用、
    或验证某行为是否合法时使用此工具。

    Args:
        query: 搜索关键词或问题描述
        category: 法律类别过滤（民法、刑法、行政法、劳动法等）
        source_type: 来源类型过滤（法律、行政法规、司法解释）
        top_k: 返回结果数量，默认5
    """
    service = LawSearchService.get_instance()
    try:
        results = await service.search(
            query,
            category=category,
            source_type=source_type,
            top_k=top_k,
        )
    except RuntimeError as e:
        return f"法律搜索出错：{e}"
    return _format_search_results(results, query)


async def get_law_article(
    ctx: RunContext[Deps],
    law_id: str,
    article_id: str,
) -> str:
    """获取指定法律的指定条文全文。当已知法律短标识和条文号时使用。

    Args:
        law_id: 法律短标识（如"民法典"、"劳动合同法"）
        article_id: 条文号（如"第四百六十四条"）
    """
    service = LawSearchService.get_instance()
    try:
        article = await service.get_article(law_id, article_id)
    except RuntimeError as e:
        return f"法律条文查询出错：{e}"
    if article is None:
        return f"未找到《{law_id}》{article_id}"
    return f"《{article.law_name}》{article.article_id}\n\n{article.content}"
