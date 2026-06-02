"""Deal-context tools + the shared ownership guard for corporate tools.

`_load_owned_deal` enforces that the active deal in `CorporateDeps`
exists and belongs to the run's user; every M&A-core tool routes through
it so a model can never reach another user's records.
"""

import json

from pydantic_ai import RunContext

from app.agents.corporate.deps import CorporateDeps
from app.db.models.corporate_deal import CorporateDeal
from app.repositories import corporate_deal_repo


def _load_owned_deal(deps: CorporateDeps) -> CorporateDeal:
    """Fetch the active deal, enforcing presence + ownership."""
    if deps.deal_id is None:
        raise RuntimeError(
            "CorporateDeps.deal_id is None — the handler must resolve the "
            "active deal before running this skill."
        )
    deal = corporate_deal_repo.get_by_id(deps.db, deps.deal_id)
    if deal is None or deal.user_id != deps.user_id:
        raise PermissionError(f"Cannot access deal {deps.deal_id} (not found, or wrong user).")
    return deal


async def read_deal_context(ctx: RunContext[CorporateDeps]) -> str:
    """读取当前交易（deal）的上下文：交易方、结构、视角、重要性阈值、数据室位置。

    并购类技能在提取问题、建表、做清单前先调用本工具，确认本单是什么、买/卖方
    视角、以及合同/诉讼的重要性阈值。

    Returns:
        JSON 字符串。
    """
    deal = _load_owned_deal(ctx.deps)
    return json.dumps(
        {
            "deal_id": deal.id,
            "code": deal.code,
            "client": deal.client,
            "counterparty": deal.counterparty,
            "deal_type": deal.deal_type,
            "side": deal.side,
            "status": deal.status,
            "key_facts": deal.key_facts,
            "dataroom_location": deal.dataroom_location,
            "materiality_contract": deal.materiality_contract,
            "materiality_litigation": deal.materiality_litigation,
        },
        ensure_ascii=False,
    )
