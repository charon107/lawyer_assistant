"""Repository for `ip_notifications`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ip_notification import IpNotification


def get_by_id(db: Session, notification_id: str) -> IpNotification | None:
    return db.get(IpNotification, notification_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[IpNotification], int]:
    base = select(IpNotification).where(IpNotification.user_id == user_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(IpNotification.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, user_id: str, title: str, **fields: Any) -> IpNotification:
    note = IpNotification(user_id=user_id, title=title, **fields)
    db.add(note)
    db.flush()
    db.refresh(note)
    return note


def mark_read(db: Session, *, notification: IpNotification) -> IpNotification:
    notification.read = True
    db.flush()
    db.refresh(notification)
    return notification
