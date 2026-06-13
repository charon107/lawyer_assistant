"""Repository for `regulatory_notifications`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.regulatory_notification import RegulatoryNotification


def get_by_id(db: Session, notification_id: str) -> RegulatoryNotification | None:
    return db.get(RegulatoryNotification, notification_id)


def list_paginated(
    db: Session,
    *,
    user_id: str,
    is_read: bool | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[RegulatoryNotification], int]:
    conditions = [RegulatoryNotification.user_id == user_id]
    if is_read is not None:
        conditions.append(RegulatoryNotification.is_read == is_read)

    total = db.execute(
        select(func.count()).select_from(RegulatoryNotification).where(*conditions)
    ).scalar_one()
    result = db.execute(
        select(RegulatoryNotification)
        .where(*conditions)
        .order_by(RegulatoryNotification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all()), total


def create(db: Session, *, user_id: str, **fields: Any) -> RegulatoryNotification:
    notification = RegulatoryNotification(user_id=user_id, **fields)
    db.add(notification)
    db.flush()
    db.refresh(notification)
    return notification


def mark_read(db: Session, *, notification: RegulatoryNotification) -> RegulatoryNotification:
    notification.is_read = True
    db.flush()
    db.refresh(notification)
    return notification
