"""RegulatoryComment request / response schemas (意见征集追踪器)."""

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

CommentDecision = Literal["undecided", "filing", "not-filing", "filed", "waived"]


class RegulatoryCommentDecide(BaseSchema):
    """`--decide`: 记录决策（filing / not-filing / filed / waived + rationale）。"""

    decision: CommentDecision
    rationale: str | None = None


class RegulatoryCommentRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    reg_item_id: str | None = None
    regulation: str | None = None
    regulator: str | None = None
    summary: str | None = None
    link: str | None = None
    comment_deadline: date | None = None
    detected: date | None = None
    decision: CommentDecision = "undecided"
    owner: str | None = None
    owner_contact: str | None = None
    notified: bool = False
    rationale: str | None = None
    filed_at: datetime | None = None
    notes: str | None = None


class RegulatoryCommentList(BaseSchema):
    items: list[RegulatoryCommentRead]
    total: int
    pending_within_30d: int = Field(default=0, description="30 天内待决定计数")
