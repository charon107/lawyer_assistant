"""Repository for `litigation_notifications`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.litigation_notification import LitigationNotification


def get_by_id(db: Session, notification_id: str) -> LitigationNotification | None:
    return db.get(LitigationNotification, notification_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[LitigationNotification], int]:
    """列表：按用户过滤，按 created_at 倒序。"""
    base = select(LitigationNotification).where(LitigationNotification.user_id == user_id)
    count_q = (
        select(func.count())
        .select_from(LitigationNotification)
        .where(LitigationNotification.user_id == user_id)
    )
    total = int(db.execute(count_q).scalar_one())
    rows = (
        db.execute(
            base.order_by(LitigationNotification.created_at.desc()).offset(skip).limit(limit)
        )
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, user_id: str, **fields: Any) -> LitigationNotification:
    notification = LitigationNotification(user_id=user_id, **fields)
    db.add(notification)
    db.flush()
    db.refresh(notification)
    return notification


def update(
    db: Session, *, notification: LitigationNotification, **fields: Any
) -> LitigationNotification:
    for key, value in fields.items():
        if value is not None:
            setattr(notification, key, value)
    db.flush()
    db.refresh(notification)
    return notification
