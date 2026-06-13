"""RegulatoryNotification service — 站内通知列表 / 标记已读."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.regulatory_notification import RegulatoryNotification
from app.repositories import regulatory_notification_repo


class RegulatoryNotificationService:
    """In-app notification list + mark-read."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_notifications(
        self, *, user_id: str, skip: int = 0, limit: int = 50
    ) -> tuple[list[RegulatoryNotification], int]:
        return regulatory_notification_repo.list_paginated(
            self.db, user_id=user_id, skip=skip, limit=limit
        )

    def mark_read(self, notification_id: str, *, user_id: str) -> RegulatoryNotification:
        notification = regulatory_notification_repo.get_by_id(self.db, notification_id)
        if notification is None or notification.user_id != user_id:
            raise NotFoundError(message="通知不存在", details={"notification_id": notification_id})
        return regulatory_notification_repo.mark_read(self.db, notification=notification)
