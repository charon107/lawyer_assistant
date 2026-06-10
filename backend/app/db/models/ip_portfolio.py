"""IpPortfolio model — a tracked IP-registration asset (知识产权组合登记册).

One row per registered asset (商标/专利/著作权/域名). The renewal-watcher
scheduled task reads these rows and recomputes the next deadline from the key
dates + per-jurisdiction rules (deadlines are NOT stored as authoritative —
they are recomputed on every report/audit/cron run, mirroring the source
plugin's "don't trust stored dates").

Analogous to commercial ``renewal_registrations``, but for IP assets.
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class IpPortfolio(Base, TimestampMixin):
    """A tracked IP-registration asset."""

    __tablename__ = "ip_portfolio"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # trademark / patent_invention / patent_utility / patent_design / copyright / domain / other
    asset_type: Mapped[str] = mapped_column(String(30), nullable=False, default="trademark")
    jurisdiction: Mapped[str | None] = mapped_column(String(60), nullable=True)  # CN / Madrid / ...
    title: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # 商标名 / 专利名 / 作品名
    owner_entity: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # pending / registered / granted / lapsed / abandoned
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="registered")

    application_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Key dates (the cron recomputes deadlines from these).
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    grant_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Cached computed deadlines (JSON list of {deadline_type, due_date, grace_end, basis_rule, ...}).
    next_deadlines: Mapped[str | None] = mapped_column(Text, nullable=True)

    business_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_managed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(30), nullable=False, default="manual"
    )  # manual / cold_start / ip_system_sync

    __table_args__ = (Index("ix_ip_portfolio_user_type", "user_id", "asset_type"),)

    def __repr__(self) -> str:
        return (
            f"<IpPortfolio(id={self.id}, type={self.asset_type}, "
            f"jurisdiction={self.jurisdiction}, status={self.status})>"
        )
