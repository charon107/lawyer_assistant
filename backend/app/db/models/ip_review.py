"""IpReview model — a saved IP analysis output.

Unified table for the six LLM-reasoning analysis skills whose outputs are
structurally similar and cross-reference each other (cross-skill severity
floor + same-subject / same-counterparty prior-context lookup):

  - clearance      (商标可注册性初筛)
  - fto            (专利自由实施初筛)
  - invention      (发明披露初筛)
  - infringement   (侵权初步分析，按 ip_category 分四态)
  - ip_clause      (合同 IP 条款审查)
  - oss            (开源许可证合规)

Written by the WS Agent skills via the ``save_review`` tool; REST only reads
the history. Enforcement letters (cease-desist / takedown) have their own
lifecycle table (``ip_enforcement``).
"""

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class IpReview(Base, TimestampMixin):
    """A saved ip-legal analysis record."""

    __tablename__ = "ip_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    review_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # clearance / fto / invention / infringement / ip_clause / oss

    # Context anchor for prior-context lookup + cross-skill severity floor.
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Skill-specific promoted columns (nullable; only set where relevant).
    # infringement: trademark / copyright / patent / trade_secret / design
    ip_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # clearance/oss: GREEN/YELLOW/RED · invention: PURSUE/INVESTIGATE/REJECT
    # infringement: IGNORE/COMMUNICATE/CEASE_DESIST/LITIGATE
    classification: Mapped[str | None] = mapped_column(String(20), nullable=True)
    severity: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # blocking / high / medium / low

    # Result
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_memo: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft / final

    __table_args__ = (Index("ix_ip_reviews_user_subject", "user_id", "subject"),)

    def __repr__(self) -> str:
        return f"<IpReview(id={self.id}, type={self.review_type}, status={self.status})>"
