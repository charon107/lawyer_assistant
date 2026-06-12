"""LitigationProfile model — 用户诉讼实务画像.

Per-user "practice profile" (CLAUDE.md equivalent) for the litigation-legal
(争议解决) module. One row per user. Mirrors the per-module profile pattern.

Domain context (公司画像 / 风险校准 / 争议画像 / 文书风格 / 2 种工作成果抬头规则)
is carried in JSON-text columns written at cold-start.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LitigationProfile(Base, TimestampMixin):
    """Per-user litigation-legal practice profile."""

    __tablename__ = "litigation_profiles"

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
    key_contacts: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 使用者 / 执业角色 / 当事人角色
    # user_role: lawyer / non_lawyer_with_counsel / non_lawyer_without
    user_role: Mapped[str] = mapped_column(String(40), nullable=False, default="lawyer")
    lawyer_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # practice_role: 企业法务 / 律所律师 / 独立执业 / 其他
    practice_role: Mapped[str] = mapped_column(String(20), nullable=False, default="企业法务")
    # party_role: 原告方 / 被告方 / 兼顾-默认原告 / 兼顾-默认被告 / 依案件而定
    party_role: Mapped[str] = mapped_column(String(20), nullable=False, default="依案件而定")

    # 集成 / 风险校准 / 争议画像 / 文书风格 (JSON text)
    integrations: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_calibration: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispute_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    doc_style: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 输出与表面 (JSON text: 工作成果抬头 2 分支 / 安静模式 / 审查备注格式 / 下一步决策树)
    output_config: Mapped[str | None] = mapped_column(Text, nullable=True)

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
            f"<LitigationProfile(id={self.id}, user_id={self.user_id}, "
            f"setup_status={self.setup_status})>"
        )
