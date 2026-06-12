"""Profile tool — read the user's litigation practice profile."""

from pydantic_ai import RunContext

from app.agents.litigation.deps import LitigationDeps
from app.repositories import litigation_profile_repo


def read_profile(ctx: RunContext[LitigationDeps]) -> str:
    """读取当前用户的诉讼实务画像（风险校准/争议画像/文书风格/当事人角色）。

    Returns:
        Markdown 格式的画像全文。如果用户尚未完成冷启动，返回提示信息。
    """
    profile = litigation_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None:
        return "## 用户尚未完成争议解决模块冷启动设置\n\n请引导用户运行冷启动访谈（/litigation/setup）。"
    return profile.profile_content or "## 画像已存在但 profile_content 为空"
