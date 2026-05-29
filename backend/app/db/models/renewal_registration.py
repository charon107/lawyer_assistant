"""RenewalRegistration database model — a tracked contract renewal deadline.

A renewal registration captures the dates that matter for deciding whether to
renew, renegotiate, or walk away from an agreement before it auto-renews. The
three computed date fields (`cancel_by_calendar`, `cancel_by_effective`,
`send_by_effective`) are stored rather than recomputed on read so the
renewal-watcher (Phase C) can query them directly.

`matter_id` links to a `CommercialMatter` when the renewal belongs to a tracked
matter; it is nullable so a standalone renewal can be registered without first
creating a matter.
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RenewalRegistration(Base, TimestampMixin):
    """A registered contract renewal with its key decision dates."""

    __tablename__ = "renewal_registrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("commercial_matters.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agreement_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Term basics.
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    auto_renew: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notice_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Computed decision deadlines (filled by renewal_calc at registration time).
    cancel_by_calendar: Mapped[date | None] = mapped_column(Date, nullable=True)
    cancel_by_effective: Mapped[date | None] = mapped_column(Date, nullable=True)
    send_by_effective: Mapped[date | None] = mapped_column(Date, nullable=True)

    # The lawyer's decision on this renewal.
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )  # pending / renew / terminate / renegotiate
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RenewalRegistration(id={self.id}, user_id={self.user_id}, "
            f"effective_date={self.effective_date}, decision={self.decision})>"
        )
