"""Policy read/draft tools for the employment-legal agent."""

import json

from pydantic_ai import RunContext

from app.agents.employment.deps import EmploymentDeps
from app.agents.employment.tools.profile_tools import _loads
from app.repositories import employment_profile_repo, employment_review_repo


async def read_current_policy(ctx: RunContext[EmploymentDeps]) -> str:
    """读取实践画像中的制度配置（制度位置、省级补充条款）作为起草/更新的基线。

    Returns:
        JSON 字符串。
    """
    profile = employment_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None:
        return json.dumps({"configured": False}, ensure_ascii=False)
    return json.dumps(
        {
            "configured": True,
            "policy_location": profile.policy_location,
            "provincial_supplements": _loads(profile.provincial_supplements),
        },
        ensure_ascii=False,
    )


async def save_draft_policy(
    ctx: RunContext[EmploymentDeps],
    title: str,
    draft_markdown: str,
    jurisdiction: str | None = None,
) -> str:
    """保存一份制度草案（policy-drafting / handbook-updates 产出时调用）。

    Args:
        title: 制度名称/主题。
        draft_markdown: 草案全文（Markdown）。
        jurisdiction: 适用省/直辖市（如适用）。

    Returns:
        JSON 字符串，含 review_id。
    """
    review = employment_review_repo.create(
        ctx.deps.db,
        user_id=ctx.deps.user_id,
        review_type="policy",
        result_status="in_progress",
        result_summary=title,
        result_memo=draft_markdown,
        jurisdiction=jurisdiction,
    )
    return json.dumps({"review_id": review.id}, ensure_ascii=False)
