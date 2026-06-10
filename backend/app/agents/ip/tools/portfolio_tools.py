"""Portfolio read tool for the ip-legal agent.

Lets infringement / clearance skills check the user's own registered rights
(e.g. "do we hold a registration for this mark?"). The portfolio itself is
maintained via REST CRUD; this is read-only for the agent.
"""

import json

from pydantic_ai import RunContext

from app.agents.ip.deps import IpDeps
from app.repositories import ip_portfolio_repo


async def read_portfolio(ctx: RunContext[IpDeps], asset_type: str = "") -> str:
    """读取用户的知识产权组合登记册（己方注册的商标/专利/著作权/域名），用于确认己方权利基础。

    Args:
        asset_type: 可选过滤（trademark/patent_invention/patent_utility/patent_design/copyright/domain）。

    Returns:
        JSON 字符串（list）。
    """
    rows, _ = ip_portfolio_repo.list_by_user(
        ctx.deps.db,
        user_id=ctx.deps.user_id,
        asset_type=asset_type or None,
    )
    items = [
        {
            "id": r.id,
            "asset_type": r.asset_type,
            "jurisdiction": r.jurisdiction,
            "title": r.title,
            "owner_entity": r.owner_entity,
            "status": r.status,
            "registration_number": r.registration_number,
        }
        for r in rows
    ]
    return json.dumps({"count": len(items), "assets": items}, ensure_ascii=False)
