"""RegulatoryProfile model — 用户监管合规实务画像.

Per-user "practice profile" (CLAUDE.md equivalent) for the regulatory-legal
(监管合规) module. One row per user. Mirrors the per-module profile pattern.

Domain context (监测清单 / 政策库索引 / 重要度阈值 / 动态源配置 / 差距响应流程 /
2 种工作成果抬头规则) is carried in JSON-text columns written at cold-start.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RegulatoryProfile(Base, TimestampMixin):
    """Per-user regulatory-legal practice profile."""

    __tablename__ = "regulatory_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # 公司画像 (JSON text)
    company_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 使用者 / 执业设置
    # user_role: lawyer / non_lawyer_with_counsel / non_lawyer_without
    user_role: Mapped[str] = mapped_column(String(40), nullable=False, default="lawyer")
    lawyer_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # practice_setting: 独立执业 / 中大型律所 / 法务内部 / 政府法援诊所
    practice_setting: Mapped[str] = mapped_column(String(20), nullable=False, default="法务内部")

    # 监测清单 / 政策库索引 / 重要度阈值 / 动态源配置 / 差距响应流程 (JSON text)
    watchlist: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_library: Mapped[str | None] = mapped_column(Text, nullable=True)
    materiality_threshold: Mapped[str | None] = mapped_column(Text, nullable=True)
    feed_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    gap_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 集成 / 输出与表面 (JSON text: 工作成果抬头 2 分支 / 安静模式 / 审阅备注格式 / 下一步决策树)
    integrations: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_config: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 监测状态：上次 feed 检查时间戳（下次 cron 从此点起；可空）
    last_feed_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 状态
    setup_depth: Mapped[str] = mapped_column(
        String(20), nullable=False, default="full"
    )  # quick / full
    setup_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="not_started"
    )  # not_started / in_progress / completed
    setup_progress: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # 编译后的 Markdown 画像（注入系统提示词）
    profile_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RegulatoryProfile(id={self.id}, user_id={self.user_id}, "
            f"setup_status={self.setup_status})>"
        )
