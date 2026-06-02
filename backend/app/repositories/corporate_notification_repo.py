"""Repository for corporate_notifications. Stateless; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.corporate_notification import CorporateNotification


def get_by_id(db: Session, notif_id: str) -> CorporateNotification | None:
    return db.get(CorporateNotification, notif_id)


def list_by_user(
    db: Session, *, user_id: str, skip: int = 0, limit: int = 50
) -> tuple[list[CorporateNotification], int]:
    base = select(CorporateNotification).where(CorporateNotification.user_id == user_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(CorporateNotification.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def count_unread(db: Session, *, user_id: str) -> int:
    rows = (
        db.execute(
            select(CorporateNotification.id).where(
                CorporateNotification.user_id == user_id,
                CorporateNotification.read.is_(False),
            )
        )
        .scalars()
        .all()
    )
    return len(rows)


def create(db: Session, *, user_id: str, title: str, **fields: Any) -> CorporateNotification:
    row = CorporateNotification(user_id=user_id, title=title, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def mark_read(db: Session, *, row: CorporateNotification) -> CorporateNotification:
    row.read = True
    db.flush()
    db.refresh(row)
    return row
