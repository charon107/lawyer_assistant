"""Material-contract schedule write tool for the corporate-legal agent."""

import json

from pydantic_ai import RunContext

from app.agents.corporate.deps import CorporateDeps
from app.agents.corporate.tools.deal_tools import _load_owned_deal
from app.repositories import material_contract_repo


async def write_material_contract_item(
    ctx: RunContext[CorporateDeps],
    contract: str,
    counterparty: str | None = None,
    threshold_basis: str | None = None,
    disclosed: bool = False,
    cite: str | None = None,
    notes: str | None = None,
    source_issue_id: str | None = None,
) -> str:
    """把一份列入披露清单的重大合同写回数据库（material-contract-schedule 每份调用一次）。

    Args:
        contract: 合同标题/类型。
        counterparty: 对方当事人。
        threshold_basis: 满足收购协议的哪项重大性条件。
        disclosed: 是否已在清单中披露。
        cite: 数据室索引。
        notes: 边界情形说明等。
        source_issue_id: 来源尽调发现 id（如有）。

    Returns:
        JSON 字符串，含 item_id。
    """
    deal = _load_owned_deal(ctx.deps)
    row = material_contract_repo.create(
        ctx.deps.db,
        deal_id=deal.id,
        contract=contract,
        counterparty=counterparty,
        threshold_basis=threshold_basis,
        disclosed=disclosed,
        cite=cite,
        notes=notes,
        source_issue_id=source_issue_id,
    )
    return json.dumps({"item_id": row.id}, ensure_ascii=False)
