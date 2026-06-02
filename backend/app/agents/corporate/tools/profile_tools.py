"""Practice-profile read tool for the corporate-legal agent."""

import json

from pydantic_ai import RunContext

from app.agents.corporate.deps import CorporateDeps
from app.repositories import corporate_profile_repo


async def read_corporate_profile(ctx: RunContext[CorporateDeps]) -> str:
    """读取用户的公司业务实践画像（实务结构、活跃模块、尽调结构/格式偏好）。

    并购类技能在做实质工作前先调用本工具，以贴合用户的实务做法。

    Returns:
        JSON 字符串；若用户尚未配置则返回 {"configured": false}。
    """
    profile = corporate_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None:
        return json.dumps({"configured": False}, ensure_ascii=False)
    return json.dumps(
        {
            "configured": profile.setup_status == "completed",
            "setup_status": profile.setup_status,
            "stage": profile.stage,
            "main_jurisdiction": profile.main_jurisdiction,
            "active_modules": profile.active_modules,
            "profile_content": profile.profile_content,
        },
        ensure_ascii=False,
    )
