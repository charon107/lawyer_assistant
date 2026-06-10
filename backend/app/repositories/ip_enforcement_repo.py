"""Repository for `ip_enforcement`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.ip_enforcement import IpEnforcement


def get_by_id(db: Session, enforcement_id: str) -> IpEnforcement | None:
    return db.get(IpEnforcement, enforcement_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    matter_type: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[IpEnforcement], int]:
    base = select(IpEnforcement).where(IpEnforcement.user_id == user_id)
    if matter_type is not None:
        base = base.where(IpEnforcement.matter_type == matter_type)
    if status is not None:
        base = base.where(IpEnforcement.status == status)

    count_q = (
        select(func.count()).select_from(IpEnforcement).where(IpEnforcement.user_id == user_id)
    )
    if matter_type is not None:
        count_q = count_q.where(IpEnforcement.matter_type == matter_type)
    if status is not None:
        count_q = count_q.where(IpEnforcement.status == status)
    total = int(db.execute(count_q).scalar_one())

    rows = (
        db.execute(base.order_by(IpEnforcement.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, user_id: str, **fields: Any) -> IpEnforcement:
    row = IpEnforcement(user_id=user_id, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def update(db: Session, *, enforcement: IpEnforcement, **fields: Any) -> IpEnforcement:
    for key, value in fields.items():
        if value is not None:
            setattr(enforcement, key, value)
    db.flush()
    db.refresh(enforcement)
    return enforcement
