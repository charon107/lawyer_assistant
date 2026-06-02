"""Closing-checklist write tool for the corporate-legal agent."""

import json
from typing import Literal

from pydantic_ai import RunContext

from app.agents.corporate.deps import CorporateDeps
from app.agents.corporate.tools.deal_tools import _load_owned_deal
from app.repositories import closing_checklist_repo

ItemType = Literal[
    "condition",
    "consent",
    "document",
    "filing",
    "shareholder_vote",
    "regulatory",
    "release",
]


async def write_checklist_item(
    ctx: RunContext[CorporateDeps],
    item: str,
    item_type: ItemType = "condition",
    basis: str | None = None,
    approval_threshold: str | None = None,
    responsible: str | None = None,
    blocking: bool = True,
    source_issue_id: str | None = None,
) -> str:
    """把一项交割检查表事项写回数据库（尽调/重大合同清单交接同意事项时调用）。

    Args:
        item: 事项描述。
        item_type: condition / consent / document / filing / shareholder_vote /
            regulatory / release。
        basis: 法定或章程来源。
        approval_threshold: 批准门槛（如"控制权变更 §12.2"/"三分之二表决权"）。
        responsible: 负责人。
        blocking: 是否阻断交割（默认 True）。
        source_issue_id: 来源尽调发现 id（如有）。

    Returns:
        JSON 字符串，含 item_id。
    """
    deal = _load_owned_deal(ctx.deps)
    row = closing_checklist_repo.create(
        ctx.deps.db,
        deal_id=deal.id,
        item=item,
        item_type=item_type,
        basis=basis,
        approval_threshold=approval_threshold,
        responsible=responsible,
        blocking=blocking,
        source_issue_id=source_issue_id,
    )
    return json.dumps({"item_id": row.id, "item_type": item_type}, ensure_ascii=False)
