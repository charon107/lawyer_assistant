"""LitigationMatter model — 案件主表.

诉讼/争议的 tracking entity. One user owns many matters. A matter groups
events (litigation_matter_events), demands (litigation_demands), and
analyses (litigation_analyses) under a single case name / case number.

Mirrors commercial_matter.py structurally, but richer: court, cause of action,
party role, risk scale, conflicts gate, outcome fields.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LitigationMatter(Base, TimestampMixin):
    """A tracked litigation / dispute matter."""

    __tablename__ = "litigation_matters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    case_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    court: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cause_of_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(255), nullable=True)

    our_side: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # plaintiff / defendant / third_party
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active / settled / dismissed / judgment_won / judgment_lost / withdrawn / closed / archived
    stage: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 庭前 / 证据交换 / 庭审 / 上诉 / 执行

    risk: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 低 / 中 / 高 / 严重
    materiality: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 已计提准备金 / 已对外披露 / 监控中 / 无
    exposure_range: Mapped[str | None] = mapped_column(String(255), nullable=True)

    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_deadline: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )  # 当前最紧迫单一期限，由 events 重算回填

    outside_counsel: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    internal_owners: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    conflicts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: 冲突排查状态

    initial_theory: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(30), nullable=False, default="manual"
    )  # manual / demand_escalation / cold_start

    # 结案字段（可空）
    closed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    final_cost: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lessons: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_litigation_matters_user_status", "user_id", "status"),
        Index("ix_litigation_matters_user_case_number", "user_id", "case_number"),
    )

    def __repr__(self) -> str:
        return (
            f"<LitigationMatter(id={self.id}, user_id={self.user_id}, "
            f"case_number={self.case_number}, status={self.status})>"
        )
