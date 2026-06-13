"""RegulatoryRegItem model — 法规动态事项（监测中枢主实体）.

监测中枢的核心实体. One user owns many reg items. cron (reg-change-monitor) or
reg-feed-watcher (WS) writes them; policy-diff reads them as input.

Review decisions baked in:
- materiality / materiality_source — 三层级阈值 + 来源（auto_rule cron 预分桶 /
  llm WS 精化 / user 手动）.
- status_verified / source_tag — C2 工具层强制溯源（LLM 无 fetch 匹配 →
  [模型知识—需验证] + status_verified=false）.
- dedup_key — cron 去重（A1：水位线仅对 ok 源前移；跨用户按 URL 去重）.
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RegulatoryRegItem(Base, TimestampMixin):
    """A tracked regulatory-development item (法规动态事项)."""

    __tablename__ = "regulatory_reg_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 标识
    regulator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # item_type: regulation 正式规章 / normative 规范性文件 / nprm 征求意见稿 /
    #            pre_rule 预征求意见调研 / enforcement 执法处罚 / guidance 监管指引 /
    #            speech 领导讲话 / settlement 和解整改 / other
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, default="other")

    # 重要度 (always 🔴 / review 🟡 / fyi 🟢)
    materiality: Mapped[str] = mapped_column(String(20), nullable=False, default="review")
    # materiality_source: auto_rule cron预分桶 / llm WS精化 / user 手动
    materiality_source: Mapped[str] = mapped_column(String(20), nullable=False, default="auto_rule")

    # 内容
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_hook: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # 日期
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    comment_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    # 来源溯源
    source_tag: Mapped[str | None] = mapped_column(String(60), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 验证（默认 false；法规现行有效已核实才 true）
    status_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 去重键（url 或 标题+机构+日期 的 hash；cron 去重用）
    dedup_key: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # status: new / triaged / diffed（已跑 policy-diff）/ archived
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new")

    __table_args__ = (
        Index("ix_regulatory_reg_items_user_materiality", "user_id", "materiality"),
        Index("ix_regulatory_reg_items_user_created", "user_id", "created_at"),
        Index("ix_regulatory_reg_items_user_dedup", "user_id", "dedup_key"),
    )

    def __repr__(self) -> str:
        return (
            f"<RegulatoryRegItem(id={self.id}, user_id={self.user_id}, "
            f"item_type={self.item_type}, materiality={self.materiality})>"
        )
