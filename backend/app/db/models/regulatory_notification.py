"""RegulatoryNotification model — 站内通知.

Mirrors litigation_notification.py / ip_notification.py. 差距分配/到期、征集截止、
周报简报均写站内（不外发；逐次发送确认天然满足"不外发"安全规则）.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RegulatoryNotification(Base, TimestampMixin):
    """An in-app regulatory notification."""

    __tablename__ = "regulatory_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # notification_type: reg_digest 周报 / gap_alert 差距到期 / comment_alert 征集截止 /
    #                    gap_assignment 负责人分配 / manual
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False, default="reg_digest")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RegulatoryNotification(id={self.id}, user_id={self.user_id}, "
            f"notification_type={self.notification_type})>"
        )
