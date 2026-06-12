"""LitigationNotification model — 争议解决模块站内通知.

Mirrors ip_notification: the docket-watcher scheduled task writes here,
and the frontend notification area reads from it.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LitigationNotification(Base, TimestampMixin):
    """An in-app litigation-legal notification."""

    __tablename__ = "litigation_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # docket_alert / deadline_alert / manual
    notification_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="docket_alert"
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<LitigationNotification(id={self.id}, "
            f"type={self.notification_type}, read={self.is_read})>"
        )
