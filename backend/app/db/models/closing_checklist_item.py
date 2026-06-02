"""ClosingChecklistItem database model — one closing-checklist line under a deal.

Backs closing-checklist. Each item tracks a condition / consent / document /
filing (or 股东表决 / 监管申报 / 解除) blocking close, who is responsible, its
legal/charter basis and approval threshold, whether it blocks closing, and
status. Items can originate from a diligence finding (`source_issue_id`).
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ClosingChecklistItem(Base, TimestampMixin):
    """A single closing-checklist item under a deal."""

    __tablename__ = "closing_checklist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("corporate_deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Optional origin diligence finding. SET NULL so removing an issue never
    # cascades into deleting checklist history.
    source_issue_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("diligence_issues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # condition / consent / document / filing / shareholder_vote / regulatory / release
    item_type: Mapped[str] = mapped_column(String(30), nullable=False, default="condition")
    item: Mapped[str] = mapped_column(Text, nullable=False)
    basis: Mapped[str | None] = mapped_column(Text, nullable=True)  # 法定/章程来源
    approval_threshold: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responsible: Mapped[str | None] = mapped_column(String(255), nullable=True)
    blocking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
    )  # open / in_progress / done / waived
    due: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ClosingChecklistItem(id={self.id}, deal_id={self.deal_id}, "
            f"item_type={self.item_type}, status={self.status})>"
        )
