"""EmploymentNotification response schemas."""

from app.schemas.base import BaseSchema, TimestampSchema


class EmploymentNotificationRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    kind: str
    title: str
    body: str | None = None
    priority: str = "normal"
    action_url: str | None = None
    read: bool = False


class EmploymentNotificationList(BaseSchema):
    items: list[EmploymentNotificationRead]
    total: int
