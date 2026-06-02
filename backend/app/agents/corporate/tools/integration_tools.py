"""Integration-task write tool for the corporate-legal agent."""

import json
from typing import Literal

from pydantic_ai import RunContext

from app.agents.corporate.deps import CorporateDeps
from app.agents.corporate.tools.deal_tools import _load_owned_deal
from app.repositories import integration_task_repo

Phase = Literal["D1", "D30", "D90", "D180"]


async def write_integration_task(
    ctx: RunContext[CorporateDeps],
    task: str,
    phase: Phase = "D30",
    owner: str | None = None,
    due: str | None = None,
) -> str:
    """把一项交割后整合任务写回数据库（integration-management 每项调用一次）。

    Args:
        task: 任务的具体动作描述。
        phase: D1 / D30 / D90 / D180。
        owner: 负责人。
        due: 截止时间。

    Returns:
        JSON 字符串，含 task_id。
    """
    deal = _load_owned_deal(ctx.deps)
    row = integration_task_repo.create(
        ctx.deps.db,
        deal_id=deal.id,
        task=task,
        phase=phase,
        owner=owner,
        due=due,
    )
    return json.dumps({"task_id": row.id, "phase": phase}, ensure_ascii=False)
