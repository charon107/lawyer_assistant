"""Service layer for IpReview (read history).

WS Agent skills write results via the ``save_review`` tool; REST uses this
service to list/get the history.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.ip_review import IpReview
from app.repositories import ip_review_repo


class IpReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_reviews(
        self,
        *,
        user_id: str,
        review_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[IpReview], int]:
        return ip_review_repo.list_by_user(
            self.db, user_id=user_id, review_type=review_type, skip=skip, limit=limit
        )

    def get_owned(self, review_id: str, *, user_id: str) -> IpReview:
        review = ip_review_repo.get_by_id(self.db, review_id)
        if review is None or review.user_id != user_id:
            raise NotFoundError(message="Review not found", details={"id": review_id})
        return review
