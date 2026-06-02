"""Governance-document write tool for the corporate-legal agent."""

import json
from typing import Literal

from pydantic_ai import RunContext

from app.agents.corporate.deps import CorporateDeps
from app.repositories import board_repo

DocKind = Literal["minutes", "resolution", "written_consent"]


async def write_board_document(
    ctx: RunContext[CorporateDeps],
    title: str,
    content: str,
    doc_kind: DocKind = "minutes",
) -> str:
    """把起草的治理文书（会议纪要 / 决议 / 书面决议）写回数据库（draft 状态）。

    board-minutes 与 written-consent 技能的最后一步。

    Args:
        title: 文书标题。
        content: 完整 Markdown 正文。
        doc_kind: minutes / resolution / written_consent。

    Returns:
        JSON 字符串，含 document_id。
    """
    row = board_repo.create_document(
        ctx.deps.db,
        user_id=ctx.deps.user_id,
        title=title,
        content=content,
        doc_kind=doc_kind,
        status="draft",
    )
    return json.dumps({"document_id": row.id, "doc_kind": doc_kind}, ensure_ascii=False)
