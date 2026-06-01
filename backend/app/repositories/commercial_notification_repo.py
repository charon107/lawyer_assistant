"""Repository for `commercial_notifications`.

In-app notifications produced by the Phase C scheduled tasks. Standard create /
get / list / delete plus `unread_count`, `mark_read`, and `mark_all_read`, which
the commercial dashboard's notification inbox uses to badge and clear alerts.
"""

from sqlalchemy import desc, func, select
from sqlalchemy import update as sa_update
from sqlalchemy.orm import Session

from app.db.models.commercial_notification import CommercialNotification


def create(
    db: Session,
    *,
    user_id: str,
    type: str,
    title: str | None = None,
    payload_json: str | None = None,
    read: bool = False,
) -> CommercialNotification:
    notification = CommercialNotification(
        user_id=user_id,
        type=type,
        title=title,
        payload_json=payload_json,
        read=read,
    )
    db.add(notification)
    db.flush()
    db.refresh(notification)
    return notification


def get_by_id(db: Session, notification_id: str) -> CommercialNotification | None:
    return db.get(CommercialNotification, notification_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[CommercialNotification], int]:
    """Return `(items, total)` for the notification inbox, newest first."""
    conditions = [CommercialNotification.user_id == user_id]
    if unread_only:
        conditions.append(CommercialNotification.read.is_(False))

    total = db.execute(
        select(func.count(CommercialNotification.id)).where(*conditions)
    ).scalar_one()
    items = (
        db.execute(
            select(CommercialNotification)
            .where(*conditions)
            .order_by(desc(CommercialNotification.created_at), desc(CommercialNotification.id))
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(items), total


def unread_count(db: Session, *, user_id: str) -> int:
    """Return the number of unread notifications for a user."""
    return db.execute(
        select(func.count(CommercialNotification.id)).where(
            CommercialNotification.user_id == user_id,
            CommercialNotification.read.is_(False),
        )
    ).scalar_one()


def mark_read(db: Session, *, notification: CommercialNotification) -> CommercialNotification:
    notification.read = True
    db.flush()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, *, user_id: str) -> int:
    """Mark every unread notification for a user as read. Returns rows updated."""
    result = db.execute(
        sa_update(CommercialNotification)
        .where(
            CommercialNotification.user_id == user_id,
            CommercialNotification.read.is_(False),
        )
        .values(read=True)
    )
    db.flush()
    return result.rowcount  # type: ignore[no-any-return, attr-defined]


def delete(db: Session, notification: CommercialNotification) -> CommercialNotification:
    db.delete(notification)
    db.flush()
    return notification
