"""Data-room (VDR) read tool for the corporate-legal agent."""

import json
import logging
from pathlib import Path

from pydantic_ai import RunContext

from app.agents.corporate.deps import CorporateDeps
from app.agents.corporate.tools.deal_tools import _load_owned_deal
from app.repositories import vdr_document_repo

logger = logging.getLogger(__name__)

# Max characters to return per document content preview.
_CONTENT_LIMIT = 4000


def _resolve_content(doc) -> str | None:  # type: ignore[no-untyped-def]
    """Get parsed text content for a VDR document.

    Priority: parsed_content in DB → parse from file on disk → None.
    """
    if doc.parsed_content:
        return doc.parsed_content

    if not doc.file_path:
        return None

    try:
        from app.core.config import settings

        media_dir = Path(getattr(settings, "MEDIA_DIR", "media"))
        full_path = media_dir / doc.file_path
        if not full_path.exists():
            return None

        data = full_path.read_bytes()

        from app.services.file_storage import classify_file
        from app.services.file_upload import FileUploadService

        file_type = classify_file("", doc.filename)
        svc = FileUploadService.__new__(FileUploadService)
        return FileUploadService.parse_content(svc, data, file_type)
    except Exception:
        logger.warning("Failed to read VDR file content for doc %s", doc.id, exc_info=True)
        return None


async def read_vdr_documents(
    ctx: RunContext[CorporateDeps],
    category: str | None = None,
    include_content: bool = True,
) -> str:
    """盘点当前交易数据室中的文档，可按需求类别过滤。

    Args:
        category: 可选，按需求清单类别过滤（如"重大合同"/"知识产权"）。
        include_content: 是否包含文件解析后的文本内容（默认 True）。

    Returns:
        JSON 字符串，含文档列表（filename / category / priority / status /
        file_path / content_preview）与总数。content_preview 是文件解析文本的
        前 4000 字符，供尽调提取和表格审查直接使用。
    """
    deal = _load_owned_deal(ctx.deps)
    docs, total = vdr_document_repo.list_by_deal(ctx.deps.db, deal_id=deal.id, limit=500)
    items = []
    for d in docs:
        if category is not None and d.category != category:
            continue
        entry: dict[str, object] = {
            "id": d.id,
            "filename": d.filename,
            "category": d.category,
            "folder": d.folder,
            "priority": d.priority,
            "status": d.status,
            "file_path": d.file_path,
        }
        if include_content:
            content = _resolve_content(d)
            if content:
                entry["content_preview"] = content[:_CONTENT_LIMIT]
                if len(content) > _CONTENT_LIMIT:
                    entry["content_truncated"] = True
            else:
                entry["content_preview"] = None
        items.append(entry)
    return json.dumps({"total": total, "documents": items}, ensure_ascii=False)
