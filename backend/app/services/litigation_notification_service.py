"""LitigationNotification service — 站内通知读写."""

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.litigation_notification import LitigationNotification
from app.repositories import litigation_notification_repo


class LitigationNotificationService:
    """In-app notification read/mark-read."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, notification_id: str, *, user_id: str) -> LitigationNotification:
        notify = litigation_notification_repo.get_by_id(self.db, notification_id)
        if notify is None:
            raise NotFoundError(message="通知不存在", details={"notification_id": notification_id})
        if notify.user_id != user_id:
            raise AuthorizationError(message="无权访问该通知")
        return notify

    def list_notifications(
        self, *, user_id: str, skip: int = 0, limit: int = 50
    ) -> tuple[list[LitigationNotification], int]:
        return litigation_notification_repo.list_by_user(
            self.db, user_id=user_id, skip=skip, limit=limit
        )

    def mark_read(self, notification_id: str, *, user_id: str) -> LitigationNotification:
        notify = self.get_owned(notification_id, user_id=user_id)
        return litigation_notification_repo.update(self.db, notification=notify, is_read=True)
