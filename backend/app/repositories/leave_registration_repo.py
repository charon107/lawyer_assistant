"""Repository for `leave_registrations`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.leave_registration import LeaveRegistration


def get_by_id(db: Session, leave_id: str) -> LeaveRegistration | None:
    return db.get(LeaveRegistration, leave_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[LeaveRegistration], int]:
    base = select(LeaveRegistration).where(LeaveRegistration.user_id == user_id)
    if status is not None:
        base = base.where(LeaveRegistration.status == status)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(LeaveRegistration.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def list_active(db: Session, *, user_id: str) -> list[LeaveRegistration]:
    rows = (
        db.execute(
            select(LeaveRegistration).where(
                LeaveRegistration.user_id == user_id,
                LeaveRegistration.status == "active",
            )
        )
        .scalars()
        .all()
    )
    return list(rows)


def create(db: Session, *, user_id: str, **fields: Any) -> LeaveRegistration:
    leave = LeaveRegistration(user_id=user_id, **fields)
    db.add(leave)
    db.flush()
    db.refresh(leave)
    return leave


def update(db: Session, *, leave: LeaveRegistration, **fields: Any) -> LeaveRegistration:
    for key, value in fields.items():
        if value is not None:
            setattr(leave, key, value)
    db.flush()
    db.refresh(leave)
    return leave


def delete(db: Session, leave_id: str) -> LeaveRegistration | None:
    leave = get_by_id(db, leave_id)
    if leave is not None:
        db.delete(leave)
        db.flush()
    return leave
