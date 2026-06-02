"""Corporate-legal in-app notification schemas."""

from app.schemas.base import BaseSchema, TimestampSchema


class CorporateNotificationRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    kind: str = "dataroom_watcher"
    title: str
    body: str | None = None
    deal_id: str | None = None
    read: bool = False


class CorporateNotificationList(BaseSchema):
    items: list[CorporateNotificationRead]
    total: int
    unread: int = 0
