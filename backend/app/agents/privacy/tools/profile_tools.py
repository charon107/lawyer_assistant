"""Practice-profile read tool + shared JSON helper for privacy tools."""

import json
from typing import Any

from pydantic_ai import RunContext

from app.agents.privacy.deps import PrivacyDeps
from app.repositories import privacy_profile_repo


def _loads(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def read_privacy_profile(ctx: RunContext[PrivacyDeps]) -> str:
    """读取当前用户的个人信息保护实践画像（监管覆盖范围、DPA 操作手册、处理规则承诺、PIA 内部规范、DSAR 流程、使用者角色）。

    每项技能开工前先调用，确认实践场景与配置。若未配置则提示用户先完成冷启动设置。

    Returns:
        JSON 字符串。
    """
    profile = privacy_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None or profile.setup_status != "completed":
        return json.dumps(
            {
                "configured": False,
                "note": "用户尚未完成个人信息保护模块的冷启动配置。请引导前往设置页面完成。",
            },
            ensure_ascii=False,
        )
    return json.dumps(
        {
            "configured": True,
            "profile_content": profile.profile_content,
            "user_role": profile.user_role,
            "regulatory_footprint": _loads(profile.regulatory_footprint),
            "dpa_playbook": _loads(profile.dpa_playbook),
            "policy_commitments": _loads(profile.policy_commitments),
            "pia_house_style": _loads(profile.pia_house_style),
            "dsar_process": _loads(profile.dsar_process),
            "escalation_matrix": _loads(profile.escalation_matrix),
            "output_config": _loads(profile.output_config),
        },
        ensure_ascii=False,
    )
