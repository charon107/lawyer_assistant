"""Repository for `employment_reviews`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.employment_review import EmploymentReview


def get_by_id(db: Session, review_id: str) -> EmploymentReview | None:
    return db.get(EmploymentReview, review_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    review_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[EmploymentReview], int]:
    base = select(EmploymentReview).where(EmploymentReview.user_id == user_id)
    if review_type is not None:
        base = base.where(EmploymentReview.review_type == review_type)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(EmploymentReview.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, user_id: str, review_type: str, **fields: Any) -> EmploymentReview:
    review = EmploymentReview(user_id=user_id, review_type=review_type, **fields)
    db.add(review)
    db.flush()
    db.refresh(review)
    return review


def update(db: Session, *, review: EmploymentReview, **fields: Any) -> EmploymentReview:
    for key, value in fields.items():
        if value is not None:
            setattr(review, key, value)
    db.flush()
    db.refresh(review)
    return review
