"""Tools that read/write the user's CommercialProfile.

`read_practice_profile`  — used at the start of any skill so the
                            agent knows who the user is and which
                            side / industry / GC they work in.
`write_practice_profile` — used by the cold-start interview to
                            persist the final Markdown profile.

PydanticAI signature note: the first parameter is the RunContext.
The body deliberately does NOT commit — the calling layer (WS
handler or HTTP route) commits when the run finishes successfully.
"""

from pydantic_ai import RunContext

from app.agents.commercial.deps import CommercialDeps
from app.repositories import commercial_profile_repo


async def read_practice_profile(ctx: RunContext[CommercialDeps]) -> str:
    """读取当前用户的「实践画像」(practice profile)。

    画像里写了用户公司是谁、做哪一侧、月均合同量、法务负责人是谁，
    以及他们的合同手册概述。在做任何审查、续约登记、上报路由之前，
    务必先调用本工具。

    Returns:
        Markdown 文本。如果用户还没完成冷启动，会返回一段提示让
        Agent 把用户引导到 cold-start 流程。
    """
    profile = commercial_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None or profile.setup_status != "completed":
        return (
            "⚠️ 当前用户尚未完成商事合同模块的冷启动配置。\n"
            "请告知用户前往「商事合同 → 设置」页面完成配置，否则无法进行有意义的审查。"
        )
    parts: list[str] = []
    parts.append(f"**公司**: {profile.company_name or '(未填写)'}")
    parts.append(f"**侧**: {profile.side}")
    if profile.gc_name:
        parts.append(f"**法务负责人**: {profile.gc_name}")
    if profile.monthly_volume:
        parts.append(f"**月均合同量**: {profile.monthly_volume}")
    parts.append("")
    if profile.profile_content:
        parts.append(profile.profile_content)
    return "\n".join(parts)


async def write_practice_profile(
    ctx: RunContext[CommercialDeps],
    profile_content: str,
) -> str:
    """写入或更新用户的「实践画像」Markdown 内容。

    仅在冷启动访谈或用户明确要求更新画像时使用。**不要**在审查中
    随手调用本工具 —— 写入会立即影响后续所有技能的系统提示词。

    Args:
        profile_content: 完整的 Markdown 画像内容。

    Returns:
        "ok" 或解释失败原因的字符串。
    """
    profile = commercial_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None:
        commercial_profile_repo.create(
            ctx.deps.db,
            user_id=ctx.deps.user_id,
            profile_content=profile_content,
            setup_status="in_progress",
        )
    else:
        commercial_profile_repo.update(
            ctx.deps.db,
            profile=profile,
            profile_content=profile_content,
        )
    return "ok"
