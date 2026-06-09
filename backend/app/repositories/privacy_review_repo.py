"""Repository for `privacy_reviews`. Stateless sync; never commits."""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.privacy_review import PrivacyReview


def get_by_id(db: Session, review_id: str) -> PrivacyReview | None:
    return db.get(PrivacyReview, review_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    review_type: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[PrivacyReview], int]:
    base = select(PrivacyReview).where(PrivacyReview.user_id == user_id)
    if review_type is not None:
        base = base.where(PrivacyReview.review_type == review_type)

    count_q = (
        select(func.count()).select_from(PrivacyReview).where(PrivacyReview.user_id == user_id)
    )
    if review_type is not None:
        count_q = count_q.where(PrivacyReview.review_type == review_type)
    total = int(db.execute(count_q).scalar_one())

    rows = (
        db.execute(base.order_by(PrivacyReview.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def list_by_subject(
    db: Session, *, user_id: str, subject: str, limit: int = 20
) -> list[PrivacyReview]:
    """Prior-context lookup — same subject (activity / counterparty)."""
    base = select(PrivacyReview).where(
        PrivacyReview.user_id == user_id, PrivacyReview.subject == subject
    )
    rows = db.execute(base.order_by(PrivacyReview.created_at.desc()).limit(limit)).scalars().all()
    return list(rows)


def count_since(
    db: Session, *, user_id: str, since: datetime | None, exclude_type: str | None = None
) -> int:
    """Count reviews created after ``since`` (for the policy-sweep reminder).

    ``exclude_type`` skips a review_type (e.g. ``policy_sweep`` so the sweep
    output itself does not inflate the next reminder).
    """
    base = select(func.count()).select_from(PrivacyReview).where(PrivacyReview.user_id == user_id)
    if since is not None:
        base = base.where(PrivacyReview.created_at > since)
    if exclude_type is not None:
        base = base.where(PrivacyReview.review_type != exclude_type)
    return int(db.execute(base).scalar_one())


def create(db: Session, *, user_id: str, review_type: str, **fields: Any) -> PrivacyReview:
    review = PrivacyReview(user_id=user_id, review_type=review_type, **fields)
    db.add(review)
    db.flush()
    db.refresh(review)
    return review


def update(db: Session, *, review: PrivacyReview, **fields: Any) -> PrivacyReview:
    for key, value in fields.items():
        if value is not None:
            setattr(review, key, value)
    db.flush()
    db.refresh(review)
    return review
