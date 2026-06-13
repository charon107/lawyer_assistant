"""RegulatoryGap model — 差距追踪器（源 gap-tracker.yaml 落库）.

regulatory 核心追踪器. policy-diff 交接创建；gaps(REST) 状态报告读写.

Review decision A3 baked in:
- regulation_citation — 稳定去重键（法条引用，§7.4 已捕获）. 去重键 =
  (regulation_citation + policy_affected)；引用缺失才回退归一化 requirement 文本.
  **不再用自由文本 requirement 作主键**（重跑 policy-diff 措辞漂移会去重失败）.

§2.4 不变量：status_verified=false 的差距即便过期也永不进 🔴 逾期.
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RegulatoryGap(Base, TimestampMixin):
    """A compliance gap tracked from policy-diff handoff."""

    __tablename__ = "regulatory_gaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reg_item_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("regulatory_reg_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    analysis_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("regulatory_analyses.id", ondelete="SET NULL"),
        nullable=True,
    )

    requirement: Mapped[str | None] = mapped_column(Text, nullable=True)  # 法规要求的内容
    regulation: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 名称 + 引用
    # A3 稳定去重键：法条引用（如《某法》第 X 条）
    regulation_citation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 政策名 或 "需要制定新政策"（字符串非 FK）
    policy_affected: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # gap_type: none / partial / full / new-policy / watch / comment-decision
    gap_type: Mapped[str] = mapped_column(String(20), nullable=False, default="partial")
    # severity: blocking / high / medium / low（携带上游严重性底线）
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)

    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)

    opened: Mapped[date | None] = mapped_column(Date, nullable=True)
    due: Mapped[date | None] = mapped_column(Date, nullable=True)

    # 上游 policy-diff 无法确认法规有效则 false；未验证永不进 🔴 逾期
    status_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # status: open / in-progress / closed / risk-accepted
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    # 负责人通知发送后 true（本期通知=站内 regulatory_notifications，不外发）
    notified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accepted_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_regulatory_gaps_user_status", "user_id", "status"),
        Index("ix_regulatory_gaps_user_due", "user_id", "due"),
    )

    def __repr__(self) -> str:
        return (
            f"<RegulatoryGap(id={self.id}, user_id={self.user_id}, "
            f"gap_type={self.gap_type}, status={self.status})>"
        )
