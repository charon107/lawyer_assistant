"""LitigationNotification request / response schemas."""

from typing import Literal

from app.schemas.base import BaseSchema, TimestampSchema

NotificationType = Literal["docket_alert", "deadline_alert", "manual"]
Priority = Literal["high", "medium", "low", "normal"]


class LitigationNotificationRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    notification_type: NotificationType = "docket_alert"
    title: str
    content: str | None = None
    priority: Priority = "normal"
    is_read: bool = False
    action_url: str | None = None


class LitigationNotificationList(BaseSchema):
    items: list[LitigationNotificationRead]
    total: int
