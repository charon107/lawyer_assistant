"""DiligenceIssue database model — one diligence finding under a deal.

Backs diligence-issue-extraction. Each finding follows the internal memo
shape: title, request-list category, severity (🔴/🟠/🟡/🟢), source
document, the finding text, and a recommendation (price adjustment /
indemnity / consent / R&W / exit). Findings can hand off to the closing
checklist and the material-contract schedule.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DiligenceIssue(Base, TimestampMixin):
    """A single diligence finding under a deal."""

    __tablename__ = "diligence_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("corporate_deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Canonical severity floor: blocking / high / medium / low (🔴/🟠/🟡/🟢).
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    source_doc: Mapped[str | None] = mapped_column(String(500), nullable=True)
    finding: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    cite: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
    )  # open / resolved / waived

    def __repr__(self) -> str:
        return f"<DiligenceIssue(id={self.id}, deal_id={self.deal_id}, severity={self.severity}, status={self.status})>"
