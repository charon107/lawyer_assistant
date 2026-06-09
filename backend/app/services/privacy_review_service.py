"""Service layer for PrivacyReview (read history).

WS Agent skills write results via the ``save_review`` tool; REST uses this
service to list/get the history.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.privacy_review import PrivacyReview
from app.repositories import privacy_review_repo


class PrivacyReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_reviews(
        self,
        *,
        user_id: str,
        review_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PrivacyReview], int]:
        return privacy_review_repo.list_by_user(
            self.db, user_id=user_id, review_type=review_type, skip=skip, limit=limit
        )

    def get_owned(self, review_id: str, *, user_id: str) -> PrivacyReview:
        review = privacy_review_repo.get_by_id(self.db, review_id)
        if review is None or review.user_id != user_id:
            raise NotFoundError(message="Review not found", details={"id": review_id})
        return review
