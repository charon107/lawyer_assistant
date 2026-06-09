"""PrivacyNotification model — in-app notifications for the privacy module.

Mirrors employment_notification: the policy-sweep-reminder scheduled task
writes here, and the frontend notification area reads from it.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class PrivacyNotification(Base, TimestampMixin):
    """An in-app privacy-legal notification."""

    __tablename__ = "privacy_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # policy_sweep_reminder / manual / system
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default="policy_sweep_reminder")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)  # Markdown
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<PrivacyNotification(id={self.id}, kind={self.kind}, read={self.read})>"
