"""Repository for `regulatory_comments`. Stateless sync; never commits."""

from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.regulatory_comment import RegulatoryComment

_OPEN_DECISIONS = ("undecided", "filing")


def get_by_id(db: Session, comment_id: str) -> RegulatoryComment | None:
    return db.get(RegulatoryComment, comment_id)


def list_open(db: Session, *, user_id: str) -> list[RegulatoryComment]:
    """Open consultations (undecided / filing) ordered by deadline."""
    result = db.execute(
        select(RegulatoryComment)
        .where(
            RegulatoryComment.user_id == user_id,
            RegulatoryComment.decision.in_(_OPEN_DECISIONS),
        )
        .order_by(RegulatoryComment.comment_deadline.asc())
    )
    return list(result.scalars().all())


def list_due_within(
    db: Session, *, user_id: str, days: int, today: date | None = None
) -> list[RegulatoryComment]:
    """Open consultations whose deadline falls within `days` (reminder cadence)."""
    ref = today or date.today()
    cutoff = ref + timedelta(days=days)
    result = db.execute(
        select(RegulatoryComment)
        .where(
            RegulatoryComment.user_id == user_id,
            RegulatoryComment.decision.in_(_OPEN_DECISIONS),
            RegulatoryComment.comment_deadline.is_not(None),
            RegulatoryComment.comment_deadline <= cutoff,
        )
        .order_by(RegulatoryComment.comment_deadline.asc())
    )
    return list(result.scalars().all())


def list_paginated(
    db: Session,
    *,
    user_id: str,
    decision: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[RegulatoryComment], int]:
    conditions = [RegulatoryComment.user_id == user_id]
    if decision is not None:
        conditions.append(RegulatoryComment.decision == decision)

    total = db.execute(
        select(func.count()).select_from(RegulatoryComment).where(*conditions)
    ).scalar_one()
    result = db.execute(
        select(RegulatoryComment)
        .where(*conditions)
        .order_by(RegulatoryComment.comment_deadline.asc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all()), total


def create(db: Session, *, user_id: str, **fields: Any) -> RegulatoryComment:
    comment = RegulatoryComment(user_id=user_id, **fields)
    db.add(comment)
    db.flush()
    db.refresh(comment)
    return comment


def update(db: Session, *, comment: RegulatoryComment, **fields: Any) -> RegulatoryComment:
    for key, value in fields.items():
        if value is not None:
            setattr(comment, key, value)
    db.flush()
    db.refresh(comment)
    return comment
