"""RegulatoryComment model — 意见征集追踪器（源 comment-tracker.yaml 落库）.

征求意见稿决策追踪. reg-feed-watcher / cron 自动录入；comments(REST) 决策记录.

提醒节奏（comments 服务 / cron 算术，非 LLM）：截止前 14 天提醒（仍 undecided）、
前 3 天提醒（升级紧急度）.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RegulatoryComment(Base, TimestampMixin):
    """A public-consultation (征求意见稿) decision tracked item."""

    __tablename__ = "regulatory_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reg_item_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("regulatory_reg_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    regulation: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 名称 + 引用
    regulator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # 一句话——此规则制定提议什么
    link: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    comment_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    detected: Mapped[date | None] = mapped_column(Date, nullable=True)  # 首次检测

    # decision: undecided / filing / not-filing / filed / waived
    decision: Mapped[str] = mapped_column(String(20), nullable=False, default="undecided")

    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 站内通知发送后 true
    notified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)  # 决策理由
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_regulatory_comments_user_decision", "user_id", "decision"),
        Index("ix_regulatory_comments_user_deadline", "user_id", "comment_deadline"),
    )

    def __repr__(self) -> str:
        return (
            f"<RegulatoryComment(id={self.id}, user_id={self.user_id}, decision={self.decision})>"
        )
