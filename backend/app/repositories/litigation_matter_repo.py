"""Repository for `litigation_matters`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.litigation_matter import LitigationMatter


def get_by_id(db: Session, matter_id: str) -> LitigationMatter | None:
    return db.get(LitigationMatter, matter_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[LitigationMatter], int]:
    """列表：按用户过滤，可选按 status 过滤。返回 (items, total)。"""
    base = select(LitigationMatter).where(LitigationMatter.user_id == user_id)
    count_q = (
        select(func.count())
        .select_from(LitigationMatter)
        .where(LitigationMatter.user_id == user_id)
    )
    if status is not None:
        base = base.where(LitigationMatter.status == status)
        count_q = count_q.where(LitigationMatter.status == status)

    total = int(db.execute(count_q).scalar_one())
    rows = (
        db.execute(base.order_by(LitigationMatter.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def list_by_case_number(db: Session, *, user_id: str, case_number: str) -> list[LitigationMatter]:
    """按案号查找（冲突门禁——代号必须存在）。"""
    return list(
        db.execute(
            select(LitigationMatter).where(
                LitigationMatter.user_id == user_id,
                LitigationMatter.case_number == case_number,
            )
        )
        .scalars()
        .all()
    )


def create(db: Session, *, user_id: str, **fields: Any) -> LitigationMatter:
    matter = LitigationMatter(user_id=user_id, **fields)
    db.add(matter)
    db.flush()
    db.refresh(matter)
    return matter


def update(db: Session, *, matter: LitigationMatter, **fields: Any) -> LitigationMatter:
    for key, value in fields.items():
        if value is not None:
            setattr(matter, key, value)
    db.flush()
    db.refresh(matter)
    return matter


def delete(db: Session, *, matter: LitigationMatter) -> LitigationMatter:
    db.delete(matter)
    db.flush()
    return matter
