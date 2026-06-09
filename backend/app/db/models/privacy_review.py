"""PrivacyReview model — a saved privacy analysis output.

Unified table for the five LLM-reasoning skills whose outputs are
structurally similar and cross-reference each other (cross-skill severity
floor + same-counterparty / same-activity prior-context lookup):

  - triage        (use-case-triage)
  - pia           (pia-generation)
  - dpa           (dpa-review)
  - gap           (reg-gap-analysis)
  - policy_sweep  (policy-monitor sweep)

Written by the WS Agent skills via the ``save_review`` tool; REST only
reads the history. DSAR has its own lifecycle table (``privacy_dsar``).
"""

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PrivacyReview(Base, TimestampMixin):
    """A saved privacy-legal analysis record."""

    __tablename__ = "privacy_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    review_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # triage / pia / dpa / gap / policy_sweep

    # Context anchor for prior-context lookup + cross-skill severity floor.
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Skill-specific promoted columns (nullable; only set where relevant).
    direction: Mapped[str | None] = mapped_column(String(20), nullable=True)  # entrusted / handler
    classification: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # PROCEED / PIA_REQUIRED / DPIA_MANDATORY / STOP
    severity: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # blocking / high / medium / low
    recommendation: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # APPROVED / WITH_CONDITIONS / CHANGES_REQUIRED / NOT_APPROVED

    # Result
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_memo: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft / final

    __table_args__ = (Index("ix_privacy_reviews_user_subject", "user_id", "subject"),)

    def __repr__(self) -> str:
        return f"<PrivacyReview(id={self.id}, type={self.review_type}, status={self.status})>"
