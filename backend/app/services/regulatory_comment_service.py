"""RegulatoryComment service — 意见征集追踪器（决策记录 + 截止聚合）."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.regulatory_comment import RegulatoryComment
from app.repositories import regulatory_comment_repo
from app.schemas.regulatory.comment import RegulatoryCommentDecide

_PENDING_WINDOW_DAYS = 30


class RegulatoryCommentService:
    """意见征集追踪器：列表聚合 + 决策记录。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, comment_id: str, *, user_id: str) -> RegulatoryComment:
        comment = regulatory_comment_repo.get_by_id(self.db, comment_id)
        if comment is None or comment.user_id != user_id:
            raise NotFoundError(message="意见征集不存在", details={"comment_id": comment_id})
        return comment

    def list_paginated(
        self, *, user_id: str, decision: str | None = None, skip: int = 0, limit: int = 50
    ) -> tuple[list[RegulatoryComment], int]:
        return regulatory_comment_repo.list_paginated(
            self.db, user_id=user_id, decision=decision, skip=skip, limit=limit
        )

    def pending_within_30d(self, user_id: str, *, today: date | None = None) -> int:
        """30 天内截止且仍待决定（undecided/filing）的计数。"""
        due = regulatory_comment_repo.list_due_within(
            self.db, user_id=user_id, days=_PENDING_WINDOW_DAYS, today=today
        )
        return len(due)

    def decide(
        self, comment_id: str, *, user_id: str, data: RegulatoryCommentDecide
    ) -> RegulatoryComment:
        """记录决策（filing/not-filing/filed/waived + rationale）。"""
        comment = self.get_owned(comment_id, user_id=user_id)
        fields: dict = {"decision": data.decision}
        if data.rationale is not None:
            fields["rationale"] = data.rationale
        if data.decision == "filed":
            fields["filed_at"] = datetime.now(UTC)
        return regulatory_comment_repo.update(self.db, comment=comment, **fields)
