"""Service layer for employment notifications (list + mark read)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.employment_notification import EmploymentNotification
from app.repositories import employment_notification_repo


class EmploymentNotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_notifications(
        self, *, user_id: str, skip: int = 0, limit: int = 50
    ) -> tuple[list[EmploymentNotification], int]:
        return employment_notification_repo.list_by_user(
            self.db, user_id=user_id, skip=skip, limit=limit
        )

    def mark_read(self, notification_id: str, *, user_id: str) -> EmploymentNotification:
        note = employment_notification_repo.get_by_id(self.db, notification_id)
        if note is None or note.user_id != user_id:
            raise NotFoundError(message="Notification not found", details={"id": notification_id})
        return employment_notification_repo.mark_read(self.db, notification=note)
