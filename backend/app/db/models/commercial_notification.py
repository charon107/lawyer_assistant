"""CommercialNotification database model — a scheduler-produced alert.

The Phase C scheduled tasks (renewal-watcher, deal-debrief, playbook-monitor)
write notifications here instead of pushing them straight to a channel, so the
commercial dashboard can surface a single in-app inbox. `payload_json` carries
the task-specific body (e.g. the list of upcoming renewals or a debrief
summary) as a JSON string; the `type` field tells the frontend how to render
it. `read` lets the lawyer dismiss an alert once acted on.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CommercialNotification(Base, TimestampMixin):
    """An in-app notification produced by a commercial scheduled task."""

    __tablename__ = "commercial_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<CommercialNotification(id={self.id}, user_id={self.user_id}, "
            f"type={self.type}, read={self.read})>"
        )
