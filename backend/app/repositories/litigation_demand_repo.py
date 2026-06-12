"""Repository for `litigation_demands`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.litigation_demand import LitigationDemand


def get_by_id(db: Session, demand_id: str) -> LitigationDemand | None:
    return db.get(LitigationDemand, demand_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    mode: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[LitigationDemand], int]:
    """列表：按用户过滤，可选按 mode/status 过滤。"""
    base = select(LitigationDemand).where(LitigationDemand.user_id == user_id)
    count_q = (
        select(func.count())
        .select_from(LitigationDemand)
        .where(LitigationDemand.user_id == user_id)
    )
    if mode is not None:
        base = base.where(LitigationDemand.mode == mode)
        count_q = count_q.where(LitigationDemand.mode == mode)
    if status is not None:
        base = base.where(LitigationDemand.status == status)
        count_q = count_q.where(LitigationDemand.status == status)

    total = int(db.execute(count_q).scalar_one())
    rows = (
        db.execute(base.order_by(LitigationDemand.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, user_id: str, **fields: Any) -> LitigationDemand:
    demand = LitigationDemand(user_id=user_id, **fields)
    db.add(demand)
    db.flush()
    db.refresh(demand)
    return demand


def update(db: Session, *, demand: LitigationDemand, **fields: Any) -> LitigationDemand:
    for key, value in fields.items():
        if value is not None:
            setattr(demand, key, value)
    db.flush()
    db.refresh(demand)
    return demand
