"""Practice-profile read tool + shared JSON helper for employment tools."""

import json
from typing import Any

from pydantic_ai import RunContext

from app.agents.employment.deps import EmploymentDeps
from app.repositories import employment_profile_repo


def _loads(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


async def read_employment_profile(ctx: RunContext[EmploymentDeps]) -> str:
    """读取当前用户的劳动用工实践画像（管辖地、默认属地、使用者角色、补偿金政策、属地规则表）。

    每个审查类技能开工前先调用，确认实践场景与属地配置。

    Returns:
        JSON 字符串。
    """
    profile = employment_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None:
        return json.dumps(
            {"configured": False, "note": "用户尚未配置劳动用工模块。"}, ensure_ascii=False
        )
    return json.dumps(
        {
            "configured": True,
            "profile_content": profile.profile_content,
            "default_jurisdiction": profile.default_jurisdiction,
            "jurisdictions": _loads(profile.jurisdictions),
            "user_role": profile.user_role,
            "standard_severance": profile.standard_severance,
            "high_risk_flags": _loads(profile.high_risk_flags),
            "jurisdiction_table": _loads(profile.jurisdiction_table),
        },
        ensure_ascii=False,
    )
