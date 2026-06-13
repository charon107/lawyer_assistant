"""RegulatoryAnalysis model — 内部分析产出统一表.

Mirrors litigation_analysis.py / ip_review.py. Discriminated by analysis_type
into 2 kinds: policy_diff / policy_redraft. Written by WS Agent via save_analysis.

Review decisions baked in:
- scope_limited / scope_note — policy-diff 范围完整性标记（大声且永久，传递下游）.
- status_verified — 法规状态是否已核实；未核实则输出加横幅.
- severity — 跨技能严重性底线（🔴 上游不得下游无声降级）.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RegulatoryAnalysis(Base, TimestampMixin):
    """A regulatory internal analysis output (policy_diff / policy_redraft)."""

    __tablename__ = "regulatory_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 可空——粘贴的法规未必有 reg_item
    reg_item_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("regulatory_reg_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    # analysis_type: policy_diff / policy_redraft
    analysis_type: Mapped[str] = mapped_column(String(30), nullable=False)
    subject: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # 法规名称（prior-context 检索）
    regulation_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    policy_affected: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # severity: blocking / high / medium / low ↔ 🔴🟠🟡🟢
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # policy-diff 范围限制标记（大声且永久，传递下游）
    scope_limited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scope_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 法规状态是否已核实（未核实则输出加横幅）
    status_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 产出
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_memo: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown 全文（含抬头）
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # 结构化

    # status: draft / final
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    __table_args__ = (
        Index("ix_regulatory_analyses_user_subject", "user_id", "subject"),
        Index("ix_regulatory_analyses_type", "analysis_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<RegulatoryAnalysis(id={self.id}, user_id={self.user_id}, "
            f"analysis_type={self.analysis_type}, status={self.status})>"
        )
