"""CorporateNotification model — in-app notifications for the corporate module.

Mirrors commercial_notification: the dataroom-watcher scheduled agent
writes here (Feishu posting is downgraded to in-app), and the frontend
notification area reads from it.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CorporateNotification(Base, TimestampMixin):
    """An in-app corporate-legal notification."""

    __tablename__ = "corporate_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # dataroom_watcher / system
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default="dataroom_watcher")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    deal_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<CorporateNotification(id={self.id}, kind={self.kind}, read={self.read})>"
