"""Policy-monitor tools for the privacy-legal agent.

The plugin's "outputs folder" maps to the ``privacy_reviews`` table:
``list_recent_reviews`` returns reviews since the profile's last sweep,
and ``save_policy_sweep`` writes the sweep report + a notification for any
REQUIRED updates and advances the last-sweep date.
"""

import json
from datetime import date, datetime
from typing import Any

from pydantic_ai import RunContext

from app.agents.privacy.deps import PrivacyDeps
from app.agents.privacy.tools.profile_tools import _loads
from app.repositories import (
    privacy_notification_repo,
    privacy_profile_repo,
    privacy_review_repo,
)


def _dump(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _parse_since(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def read_policy_commitments(ctx: RunContext[PrivacyDeps]) -> str:
    """读取当前处理规则承诺 + 各承诺表面位置 + 上次扫描日期。

    Returns:
        JSON 字符串。
    """
    profile = privacy_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is None:
        return json.dumps({"configured": False}, ensure_ascii=False)
    return json.dumps(
        {
            "configured": True,
            "regulatory_footprint": _loads(profile.regulatory_footprint),
            "policy_commitments": _loads(profile.policy_commitments),
            "output_config": _loads(profile.output_config),
        },
        ensure_ascii=False,
    )


async def list_recent_reviews(ctx: RunContext[PrivacyDeps]) -> str:
    """读取自上次处理规则扫描以来的分析产出（PIA/DPA/分诊），用于扫描模式漂移比对。

    Returns:
        JSON 字符串（list）。
    """
    profile = privacy_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    output_config = _loads(profile.output_config) if profile else None
    since = (
        _parse_since(output_config.get("last_policy_sweep"))
        if isinstance(output_config, dict)
        else None
    )

    rows, _ = privacy_review_repo.list_by_user(ctx.deps.db, user_id=ctx.deps.user_id, limit=200)
    items = []
    for r in rows:
        if r.review_type == "policy_sweep":
            continue
        if since is not None and r.created_at is not None and r.created_at <= since:
            continue
        items.append(
            {
                "id": r.id,
                "review_type": r.review_type,
                "subject": r.subject,
                "summary": r.result_summary,
                "result_json": _loads(r.result_json),
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return json.dumps(
        {"since": since.isoformat() if since else None, "count": len(items), "reviews": items},
        ensure_ascii=False,
    )


async def save_policy_sweep(
    ctx: RunContext[PrivacyDeps],
    result_summary: str,
    result_memo: str | None = None,
    result_json: dict[str, Any] | None = None,
    required_count: int = 0,
) -> str:
    """写处理规则扫描报告（review type=policy_sweep）；对必须更新项发通知；并推进上次扫描日期。

    Args:
        result_summary: 扫描结论。
        result_memo: 完整扫描报告（Markdown）。
        result_json: {required:[...], advisable:[...]}。
        required_count: 必须更新项数量（>0 时发通知）。

    Returns:
        JSON 字符串。
    """
    review = privacy_review_repo.create(
        ctx.deps.db,
        user_id=ctx.deps.user_id,
        review_type="policy_sweep",
        subject="处理规则扫描",
        result_summary=result_summary,
        result_memo=result_memo,
        result_json=_dump(result_json),
        status="final",
    )

    if required_count > 0:
        privacy_notification_repo.create(
            ctx.deps.db,
            user_id=ctx.deps.user_id,
            kind="manual",
            title=f"处理规则扫描发现 {required_count} 项必须更新",
            body=result_summary,
            priority="high",
            action_url=f"/privacy/reviews/{review.id}",
        )

    # Advance last-sweep date in the profile's output_config.
    profile = privacy_profile_repo.get_by_user_id(ctx.deps.db, ctx.deps.user_id)
    if profile is not None:
        output_config = _loads(profile.output_config)
        if not isinstance(output_config, dict):
            output_config = {}
        output_config["last_policy_sweep"] = date.today().isoformat()
        privacy_profile_repo.update(
            ctx.deps.db,
            profile=profile,
            output_config=json.dumps(output_config, ensure_ascii=False),
        )

    return json.dumps(
        {"review_id": review.id, "required_count": required_count}, ensure_ascii=False
    )
