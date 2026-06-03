"""Repository for `employment_expansions`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.employment_expansion import EmploymentExpansion


def get_by_id(db: Session, expansion_id: str) -> EmploymentExpansion | None:
    return db.get(EmploymentExpansion, expansion_id)


def get_by_slug(db: Session, *, user_id: str, slug: str) -> EmploymentExpansion | None:
    result = db.execute(
        select(EmploymentExpansion).where(
            EmploymentExpansion.user_id == user_id,
            EmploymentExpansion.slug == slug,
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
) -> tuple[list[EmploymentExpansion], int]:
    base = select(EmploymentExpansion).where(EmploymentExpansion.user_id == user_id)
    if status is not None:
        base = base.where(EmploymentExpansion.status == status)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(EmploymentExpansion.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(
    db: Session, *, user_id: str, slug: str, province: str, **fields: Any
) -> EmploymentExpansion:
    exp = EmploymentExpansion(user_id=user_id, slug=slug, province=province, **fields)
    db.add(exp)
    db.flush()
    db.refresh(exp)
    return exp


def update(db: Session, *, expansion: EmploymentExpansion, **fields: Any) -> EmploymentExpansion:
    for key, value in fields.items():
        if value is not None:
            setattr(expansion, key, value)
    db.flush()
    db.refresh(expansion)
    return expansion
