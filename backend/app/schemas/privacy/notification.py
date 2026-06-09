"""PrivacyNotification response schemas."""

from app.schemas.base import BaseSchema, TimestampSchema


class PrivacyNotificationRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    kind: str
    title: str
    body: str | None = None
    priority: str = "normal"
    action_url: str | None = None
    read: bool = False


class PrivacyNotificationList(BaseSchema):
    items: list[PrivacyNotificationRead]
    total: int
