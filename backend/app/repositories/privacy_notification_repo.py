"""Repository for `privacy_notifications`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.privacy_notification import PrivacyNotification


def get_by_id(db: Session, notification_id: str) -> PrivacyNotification | None:
    return db.get(PrivacyNotification, notification_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[PrivacyNotification], int]:
    base = select(PrivacyNotification).where(PrivacyNotification.user_id == user_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(PrivacyNotification.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, user_id: str, title: str, **fields: Any) -> PrivacyNotification:
    note = PrivacyNotification(user_id=user_id, title=title, **fields)
    db.add(note)
    db.flush()
    db.refresh(note)
    return note


def mark_read(db: Session, *, notification: PrivacyNotification) -> PrivacyNotification:
    notification.read = True
    db.flush()
    db.refresh(notification)
    return notification
