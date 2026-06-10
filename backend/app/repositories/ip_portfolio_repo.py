"""Repository for `ip_portfolio`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.ip_portfolio import IpPortfolio


def get_by_id(db: Session, asset_id: str) -> IpPortfolio | None:
    return db.get(IpPortfolio, asset_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    asset_type: str | None = None,
    skip: int = 0,
    limit: int = 1000,
) -> tuple[list[IpPortfolio], int]:
    base = select(IpPortfolio).where(IpPortfolio.user_id == user_id)
    if asset_type is not None:
        base = base.where(IpPortfolio.asset_type == asset_type)

    count_q = select(func.count()).select_from(IpPortfolio).where(IpPortfolio.user_id == user_id)
    if asset_type is not None:
        count_q = count_q.where(IpPortfolio.asset_type == asset_type)
    total = int(db.execute(count_q).scalar_one())

    rows = (
        db.execute(base.order_by(IpPortfolio.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, user_id: str, **fields: Any) -> IpPortfolio:
    row = IpPortfolio(user_id=user_id, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def update(db: Session, *, asset: IpPortfolio, **fields: Any) -> IpPortfolio:
    for key, value in fields.items():
        if value is not None:
            setattr(asset, key, value)
    db.flush()
    db.refresh(asset)
    return asset
