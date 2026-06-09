"""Repository for `privacy_dsar`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.privacy_dsar import PrivacyDsar


def get_by_id(db: Session, dsar_id: str) -> PrivacyDsar | None:
    return db.get(PrivacyDsar, dsar_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[PrivacyDsar], int]:
    base = select(PrivacyDsar).where(PrivacyDsar.user_id == user_id)
    if status is not None:
        base = base.where(PrivacyDsar.status == status)

    count_q = select(func.count()).select_from(PrivacyDsar).where(PrivacyDsar.user_id == user_id)
    if status is not None:
        count_q = count_q.where(PrivacyDsar.status == status)
    total = int(db.execute(count_q).scalar_one())

    rows = (
        db.execute(base.order_by(PrivacyDsar.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, user_id: str, **fields: Any) -> PrivacyDsar:
    dsar = PrivacyDsar(user_id=user_id, **fields)
    db.add(dsar)
    db.flush()
    db.refresh(dsar)
    return dsar


def update(db: Session, *, dsar: PrivacyDsar, **fields: Any) -> PrivacyDsar:
    for key, value in fields.items():
        if value is not None:
            setattr(dsar, key, value)
    db.flush()
    db.refresh(dsar)
    return dsar
