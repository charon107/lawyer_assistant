"""Repository for `ip_reviews`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.ip_review import IpReview


def get_by_id(db: Session, review_id: str) -> IpReview | None:
    return db.get(IpReview, review_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    review_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[IpReview], int]:
    base = select(IpReview).where(IpReview.user_id == user_id)
    if review_type is not None:
        base = base.where(IpReview.review_type == review_type)

    count_q = select(func.count()).select_from(IpReview).where(IpReview.user_id == user_id)
    if review_type is not None:
        count_q = count_q.where(IpReview.review_type == review_type)
    total = int(db.execute(count_q).scalar_one())

    rows = (
        db.execute(base.order_by(IpReview.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def list_by_subject(db: Session, *, user_id: str, subject: str, limit: int = 20) -> list[IpReview]:
    """Prior-context lookup — same subject (mark / product / counterparty)."""
    base = select(IpReview).where(IpReview.user_id == user_id, IpReview.subject == subject)
    rows = db.execute(base.order_by(IpReview.created_at.desc()).limit(limit)).scalars().all()
    return list(rows)


def create(db: Session, *, user_id: str, review_type: str, **fields: Any) -> IpReview:
    review = IpReview(user_id=user_id, review_type=review_type, **fields)
    db.add(review)
    db.flush()
    db.refresh(review)
    return review


def update(db: Session, *, review: IpReview, **fields: Any) -> IpReview:
    for key, value in fields.items():
        if value is not None:
            setattr(review, key, value)
    db.flush()
    db.refresh(review)
    return review
