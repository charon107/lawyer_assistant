"""Repository for `regulatory_gaps`. Stateless sync; never commits.

A3 review decision: dedup key = (regulation_citation + policy_affected) when a
citation exists; fall back to normalized requirement text only when citation is
absent. Free-text requirement is NOT the primary dedup key.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.regulatory_gap import RegulatoryGap

_OPEN_STATUSES = ("open", "in-progress")


def get_by_id(db: Session, gap_id: str) -> RegulatoryGap | None:
    return db.get(RegulatoryGap, gap_id)


def list_open(db: Session, *, user_id: str) -> list[RegulatoryGap]:
    """Open + in-progress gaps (status report + cron open-count). Excludes closed/risk-accepted."""
    result = db.execute(
        select(RegulatoryGap)
        .where(RegulatoryGap.user_id == user_id, RegulatoryGap.status.in_(_OPEN_STATUSES))
        .order_by(RegulatoryGap.due.asc())
    )
    return list(result.scalars().all())


def find_duplicate(
    db: Session,
    *,
    user_id: str,
    policy_affected: str | None,
    regulation_citation: str | None = None,
    requirement_normalized: str | None = None,
) -> RegulatoryGap | None:
    """A3: dedup on (citation + policy_affected); fall back to normalized requirement.

    Returns an existing non-closed gap that matches, or None.
    """
    conditions = [
        RegulatoryGap.user_id == user_id,
        RegulatoryGap.policy_affected == policy_affected,
        RegulatoryGap.status.in_(_OPEN_STATUSES),
    ]
    if regulation_citation:
        conditions.append(RegulatoryGap.regulation_citation == regulation_citation)
    elif requirement_normalized:
        # 引用缺失才回退到归一化 requirement 文本
        conditions.append(func.trim(RegulatoryGap.requirement) == requirement_normalized)
    else:
        return None

    result = db.execute(select(RegulatoryGap).where(*conditions))
    return result.scalars().first()


def list_paginated(
    db: Session,
    *,
    user_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[RegulatoryGap], int]:
    conditions = [RegulatoryGap.user_id == user_id]
    if status is not None:
        conditions.append(RegulatoryGap.status == status)

    total = db.execute(
        select(func.count()).select_from(RegulatoryGap).where(*conditions)
    ).scalar_one()
    result = db.execute(
        select(RegulatoryGap)
        .where(*conditions)
        .order_by(RegulatoryGap.due.asc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all()), total


def create(db: Session, *, user_id: str, **fields: Any) -> RegulatoryGap:
    gap = RegulatoryGap(user_id=user_id, **fields)
    db.add(gap)
    db.flush()
    db.refresh(gap)
    return gap


def update(db: Session, *, gap: RegulatoryGap, **fields: Any) -> RegulatoryGap:
    for key, value in fields.items():
        if value is not None:
            setattr(gap, key, value)
    db.flush()
    db.refresh(gap)
    return gap
