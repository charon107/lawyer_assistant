"""Data-room (VDR) read tool for the corporate-legal agent."""

import json

from pydantic_ai import RunContext

from app.agents.corporate.deps import CorporateDeps
from app.agents.corporate.tools.deal_tools import _load_owned_deal
from app.repositories import vdr_document_repo


async def read_vdr_documents(
    ctx: RunContext[CorporateDeps],
    category: str | None = None,
) -> str:
    """盘点当前交易数据室中的文档，可按需求类别过滤。

    Args:
        category: 可选，按需求清单类别过滤（如"重大合同"/"知识产权"）。

    Returns:
        JSON 字符串，含文档列表（filename / category / priority / status / file_path）
        与总数。每条是一份数据室文件——映射到需求类别并标注缺口由调用方完成。
    """
    deal = _load_owned_deal(ctx.deps)
    docs, total = vdr_document_repo.list_by_deal(ctx.deps.db, deal_id=deal.id, limit=500)
    items = [
        {
            "id": d.id,
            "filename": d.filename,
            "category": d.category,
            "folder": d.folder,
            "priority": d.priority,
            "status": d.status,
            "file_path": d.file_path,
        }
        for d in docs
        if category is None or d.category == category
    ]
    return json.dumps({"total": total, "documents": items}, ensure_ascii=False)
