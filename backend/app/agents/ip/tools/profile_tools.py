"""Practice-profile read tool + shared JSON helper for ip-legal tools."""

import json
from typing import Any

from pydantic_ai import RunContext

from app.agents.ip.deps import IpDeps
from app.repositories import ip_profile_repo


def _loads(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def read_ip_profile(ctx: RunContext[IpDeps]) -> str:
    """读取当前用户的知识产权实务画像（角色、IP 业务领域组合、注册管辖域、维权姿态+发函审批矩阵、品牌监测、工作成果抬头规则）。

    每项技能开工前先调用，确认实践场景与配置。**4 种工作成果抬头按 user_role × 事项类型分支**
    （律师 / 专利代理师-CNIPA专利事项-特权 / 专利代理师-非专利事项-非特权 / 非律师）。
    若未配置则提示用户先完成冷启动设置。

    Returns:
        JSON 字符串。
    """
    profile = ip_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None or profile.setup_status != "completed":
        return json.dumps(
            {
                "configured": False,
                "note": "用户尚未完成知识产权模块的冷启动配置。请引导前往设置页面完成。",
            },
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "configured": True,
            "profile_content": profile.profile_content,
            "user_role": profile.user_role,
            "ip_scope": _loads(profile.ip_scope),
            "registration_jurisdictions": _loads(profile.registration_jurisdictions),
            "domain_ownership": _loads(profile.domain_ownership),
            "outside_counsel": _loads(profile.outside_counsel),
            "enforcement_posture": _loads(profile.enforcement_posture),
            "brand_protection": _loads(profile.brand_protection),
            "output_config": _loads(profile.output_config),
        },
        ensure_ascii=False,
    )
