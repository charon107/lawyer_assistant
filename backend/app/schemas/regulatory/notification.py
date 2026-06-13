"""RegulatoryNotification response schemas."""

from typing import Literal

from app.schemas.base import BaseSchema, TimestampSchema

NotificationType = Literal["reg_digest", "gap_alert", "comment_alert", "gap_assignment", "manual"]
Priority = Literal["high", "medium", "low", "normal"]


class RegulatoryNotificationRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    notification_type: NotificationType = "reg_digest"
    title: str
    content: str | None = None
    priority: Priority = "normal"
    is_read: bool = False
    action_url: str | None = None


class RegulatoryNotificationList(BaseSchema):
    items: list[RegulatoryNotificationRead]
    total: int
