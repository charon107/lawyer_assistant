"""LitigationAnalysis model — 内部分析产出统一表.

Unified table for the 9 analysis-type WS Agent skills whose outputs are
structurally similar and cross-reference each other (cross-skill severity
floor + same-subject / same-matter prior-context lookup):

  analysis_type: matter_briefing / chronology / claim_chart / subpoena_triage /
                  legal_hold / oc_status / brief_section / deposition_prep /
                  privilege_log

Written by WS Agent skills via save_analysis tool; REST reads history.
Demand letters (demand_draft / demand_received) use litigation_demands.
"""

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LitigationAnalysis(Base, TimestampMixin):
    """A saved litigation-legal analysis record."""

    __tablename__ = "litigation_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("litigation_matters.id", ondelete="SET NULL"),
        nullable=True,
    )

    # 9 types: matter_briefing / chronology / claim_chart / subpoena_triage /
    #           legal_hold / oc_status / brief_section / deposition_prep / privilege_log
    analysis_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # Context anchor for prior-context lookup + cross-skill severity floor.
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Skill-specific classification (nullable; only set where relevant).
    # subpoena: 5 categories · privilege: ADMISSIBLE/MARKED/INADMISSIBLE
    # claim_chart: infringement/invalidity/civil_elements
    classification: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # blocking / high / medium / low ↔ 严重 / 优先 / 常规 / 监控
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Result
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_memo: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown, 含工作成果抬头
    # JSON: events / claim_mapping / objection_frameworks / evidence_entries /
    #       outline / legal_hold 的 hold_status + next_refresh + custodians
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
    )  # draft / final

    __table_args__ = (
        Index("ix_litigation_analyses_user_matter", "user_id", "matter_id"),
        Index("ix_litigation_analyses_type", "analysis_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<LitigationAnalysis(id={self.id}, type={self.analysis_type}, status={self.status})>"
        )
