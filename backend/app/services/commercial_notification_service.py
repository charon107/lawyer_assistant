"""Service layer for CommercialNotification.

Notifications are *created* by the Phase C scheduled tasks (renewal-watcher,
deal-debrief, playbook-monitor). The REST surface is read-and-clear only: list
with an unread badge count, mark one read, mark all read. Per-user isolation is
enforced the same way as the other commercial services — a user can never read
or mutate another user's notifications.

Repository calls never commit; the FastAPI session dependency owns commits.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.commercial_notification import CommercialNotification
from app.repositories import commercial_notification_repo as notif_repo


class CommercialNotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_my_notifications(
        self,
        user_id: str,
        *,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CommercialNotification], int, int]:
        """Paginated inbox for the current user.

        Returns `(items, total, unread)` — the unread count always reflects all
        of the user's unread notifications, independent of the page or filter,
        so the frontend badge stays correct.
        """
        items, total = notif_repo.list_by_user(
            self.db,
            user_id=user_id,
            unread_only=unread_only,
            skip=skip,
            limit=limit,
        )
        unread = notif_repo.unread_count(self.db, user_id=user_id)
        return items, total, unread

    def unread_count(self, user_id: str) -> int:
        """Number of unread notifications for the current user (badge count)."""
        return notif_repo.unread_count(self.db, user_id=user_id)

    def mark_read(self, user_id: str, notification_id: str) -> CommercialNotification:
        """Mark one owned notification read.

        Raises:
            NotFoundError: row doesn't exist.
            AuthorizationError: row exists but belongs to a different user.
        """
        notification = notif_repo.get_by_id(self.db, notification_id)
        if notification is None:
            raise NotFoundError(
                message="Notification not found",
                details={"notification_id": notification_id},
            )
        if notification.user_id != user_id:
            raise AuthorizationError(message="You do not have access to this notification")
        return notif_repo.mark_read(self.db, notification=notification)

    def mark_all_read(self, user_id: str) -> int:
        """Mark every unread notification for the current user read. Returns count."""
        return notif_repo.mark_all_read(self.db, user_id=user_id)
