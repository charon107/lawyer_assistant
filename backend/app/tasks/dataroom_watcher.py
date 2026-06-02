"""Dataroom-watcher scheduled task (corporate-legal).

Daily sweep: for each active user, scan every active deal's VDR for newly
uploaded documents (status == "new"), flag high-priority categories
(重大合同 / 诉讼 / 知识产权), summarize closing-checklist blocking status, and
write an in-app CorporateNotification. Feishu posting is downgraded to the
in-app notification per the approved plan.

Entry point `run(db)` is invoked by the scheduler wrapper which owns the
session + commit.
"""

import logging

from sqlalchemy.orm import Session

from app.repositories import (
    closing_checklist_repo,
    corporate_deal_repo,
    corporate_notification_repo,
    vdr_document_repo,
)
from app.tasks._common import iter_active_user_ids

logger = logging.getLogger(__name__)

_HIGH_PRIORITY_HINTS = ("重大合同", "诉讼", "知识产权", "IP")


def _is_high_priority(doc) -> bool:  # type: ignore[no-untyped-def]
    if doc.priority == "high":
        return True
    cat = doc.category or ""
    return any(h in cat for h in _HIGH_PRIORITY_HINTS)


def run(db: Session) -> int:
    """Run the watcher for all active users. Returns the number of notifications written."""
    written = 0
    for user_id in iter_active_user_ids(db):
        deals, _ = corporate_deal_repo.list_by_user(db, user_id=user_id, status="active", limit=200)
        for deal in deals:
            new_docs, _ = vdr_document_repo.list_by_deal(
                db, deal_id=deal.id, status="new", limit=500
            )
            if not new_docs:
                continue
            high = [d for d in new_docs if _is_high_priority(d)]
            checklist, _ = closing_checklist_repo.list_by_deal(db, deal_id=deal.id, limit=500)
            blocking_open = [
                c for c in checklist if c.blocking and c.status in ("open", "in_progress")
            ]

            lines = [
                f"**{deal.code}** 数据室有 {len(new_docs)} 份新文档待审。",
            ]
            if high:
                lines.append(
                    "高优先级（重大合同 / 诉讼 / 知识产权）："
                    + "、".join(d.filename for d in high[:10])
                )
            if blocking_open:
                lines.append(f"交割检查表仍有 {len(blocking_open)} 项阻断事项未完成。")

            corporate_notification_repo.create(
                db,
                user_id=user_id,
                kind="dataroom_watcher",
                title=f"数据室更新 · {deal.code}（{len(new_docs)} 新文档）",
                body="\n\n".join(lines),
                deal_id=deal.id,
            )
            written += 1
    logger.info("dataroom_watcher wrote %d notifications", written)
    return written
