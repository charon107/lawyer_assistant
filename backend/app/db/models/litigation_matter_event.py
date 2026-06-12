"""LitigationMatterEvent model — 案件事件流/时间线.

Each event is an entry in the matter's timeline. Pure append-only; corrections
are new entries. Derived from the source plugin's history.md per-matter event
log + _log.yaml status changes.

event_type=deadline rows feed the docket-watcher cron. due_date and
deadline_status are set for deadline-type events.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LitigationMatterEvent(Base, TimestampMixin):
    """A single event in a litigation matter's timeline."""

    __tablename__ = "litigation_matter_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    matter_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("litigation_matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # procedure / evidence / substantive / strategy / risk_reassessment /
    # party / administrative / deadline / closing
    event_type: Mapped[str] = mapped_column(String(20), nullable=False, default="procedure")

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON: {field_name: [old_value, new_value]}
    field_changes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # deadline-type events only
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # pending / approaching / overdue / met / waived

    # JSON list of associated file paths
    associated_files: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_matter_events_matter_date", "matter_id", "event_date"),)

    def __repr__(self) -> str:
        return (
            f"<LitigationMatterEvent(id={self.id}, matter_id={self.matter_id}, "
            f"event_type={self.event_type})>"
        )
