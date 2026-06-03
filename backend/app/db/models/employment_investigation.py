"""Internal-investigation models (structured).

Four tables preserve the source plugin's queryable structure so
investigation-query / -memo keep their power (cite entry refs, surface
contradiction chains, check coverage against the sources checklist):

- EmploymentInvestigation  matter header (+ compiled memo)
- InvestigationLogEntry     per-entry log (interview / document / note / gap)
- InvestigationSource       sources checklist (seeded by investigation type)
- InvestigationGap          evidentiary gaps
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class EmploymentInvestigation(Base, TimestampMixin):
    """Internal-investigation matter header."""

    __tablename__ = "employment_investigations"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "investigation_name", name="uq_employment_investigations_user_name"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    investigation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    allegation: Mapped[str | None] = mapped_column(Text, nullable=True)
    # HR / financial / executive / whistleblower / other
    investigation_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # open / investigating / memo_draft / closed
    attorney_directed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    privilege_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    log_entries: Mapped[list["InvestigationLogEntry"]] = relationship(
        "InvestigationLogEntry",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="InvestigationLogEntry.entry_seq",
    )
    sources: Mapped[list["InvestigationSource"]] = relationship(
        "InvestigationSource",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="InvestigationSource.source_seq",
    )
    gaps: Mapped[list["InvestigationGap"]] = relationship(
        "InvestigationGap",
        back_populates="investigation",
        cascade="all, delete-orphan",
        order_by="InvestigationGap.gap_seq",
    )

    def __repr__(self) -> str:
        return f"<EmploymentInvestigation(id={self.id}, name={self.investigation_name}, status={self.status})>"


class InvestigationLogEntry(Base, TimestampMixin):
    """One structured entry in an investigation log."""

    __tablename__ = "investigation_log_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employment_investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    entry_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    # interview / document / attorney-note / gap
    entry_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    date_of_event: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    issues: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    significance: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # high/medium/background
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    contradicts_entry_seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    corroborates_entry_seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pull_criterion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    privilege: Mapped[str | None] = mapped_column(String(60), nullable=True)

    investigation: Mapped["EmploymentInvestigation"] = relationship(
        "EmploymentInvestigation", back_populates="log_entries"
    )

    def __repr__(self) -> str:
        return (
            f"<InvestigationLogEntry(id={self.id}, seq={self.entry_seq}, type={self.entry_type})>"
        )


class InvestigationSource(Base, TimestampMixin):
    """A sources-checklist row, seeded by investigation type."""

    __tablename__ = "investigation_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employment_investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )  # open / in-progress / complete / na
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    investigation: Mapped["EmploymentInvestigation"] = relationship(
        "EmploymentInvestigation", back_populates="sources"
    )

    def __repr__(self) -> str:
        return f"<InvestigationSource(id={self.id}, seq={self.source_seq}, status={self.status})>"


class InvestigationGap(Base, TimestampMixin):
    """An evidentiary gap (a source that should exist but hasn't appeared)."""

    __tablename__ = "investigation_gaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("employment_investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gap_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    identified_from: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_to_obtain: Mapped[str | None] = mapped_column(String(500), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")

    investigation: Mapped["EmploymentInvestigation"] = relationship(
        "EmploymentInvestigation", back_populates="gaps"
    )

    def __repr__(self) -> str:
        return f"<InvestigationGap(id={self.id}, seq={self.gap_seq}, priority={self.priority})>"
