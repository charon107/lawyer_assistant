"""Repository for `corporate_deals`. Stateless sync functions; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.corporate_deal import CorporateDeal


def get_by_id(db: Session, deal_id: str) -> CorporateDeal | None:
    return db.get(CorporateDeal, deal_id)


def get_by_code(db: Session, *, user_id: str, code: str) -> CorporateDeal | None:
    result = db.execute(
        select(CorporateDeal).where(
            CorporateDeal.user_id == user_id,
            CorporateDeal.code == code,
        )
    )
    return result.scalar_one_or_none()


def list_by_user(
    db: Session,
    *,
    user_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[CorporateDeal], int]:
    base = select(CorporateDeal).where(CorporateDeal.user_id == user_id)
    if status is not None:
        base = base.where(CorporateDeal.status == status)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(CorporateDeal.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, user_id: str, code: str, **fields: Any) -> CorporateDeal:
    deal = CorporateDeal(user_id=user_id, code=code, **fields)
    db.add(deal)
    db.flush()
    db.refresh(deal)
    return deal


def update(db: Session, *, deal: CorporateDeal, **fields: Any) -> CorporateDeal:
    for key, value in fields.items():
        if value is not None:
            setattr(deal, key, value)
    db.flush()
    db.refresh(deal)
    return deal


def delete(db: Session, deal_id: str) -> CorporateDeal | None:
    deal = get_by_id(db, deal_id)
    if deal is not None:
        db.delete(deal)
        db.flush()
    return deal
