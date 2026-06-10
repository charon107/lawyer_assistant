"""IpNotification model — in-app notifications for the ip-legal module.

Mirrors privacy_notification: the renewal-watcher scheduled task writes here,
and the frontend notification area reads from it.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class IpNotification(Base, TimestampMixin):
    """An in-app ip-legal notification."""

    __tablename__ = "ip_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # renewal_alert / manual / system
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default="renewal_alert")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<IpNotification(id={self.id}, kind={self.kind}, read={self.read})>"
