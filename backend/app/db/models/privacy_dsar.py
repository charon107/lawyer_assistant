"""PrivacyDsar model — an individual data-subject-rights request (个人信息主体权利请求).

Distinct lifecycle from ``privacy_reviews``: two-letter response (ack +
substantive), statutory/SLA deadline, exemption analysis, audit log.

PII minimization: ``data_subject_ref`` holds a minimal identifier — never
store the subject's full name in a filename or primary key (per the source
skill's PII-handling requirement).

Created by REST intake (``POST /privacy/dsar``); the WS ``dsar`` skill
drafts the two letters and writes them back.
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PrivacyDsar(Base, TimestampMixin):
    """A data-subject-rights request record."""

    __tablename__ = "privacy_dsar"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rights invoked — JSON list of: access/copy/delete/correct/explain/restrict
    # (个保法第 44-50 条). Can be a combination.
    request_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_subject_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Dates
    date_received: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_responded: Mapped[date | None] = mapped_column(Date, nullable=True)
    response_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Identity verification
    identity_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verification_method: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Location + exemptions (JSON)
    systems_checked: Mapped[str | None] = mapped_column(Text, nullable=True)
    exemptions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Two letters (Markdown). Outbound — no work-product header.
    ack_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_letter: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="received"
    )  # received/verifying/locating/exemption_analysis/drafted/responded/escalated

    escalation_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit log (JSON): received/verified/responded dates, produced/deleted, exemptions, handler.
    log: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<PrivacyDsar(id={self.id}, status={self.status})>"
