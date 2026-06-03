"""Service layer for EmploymentReview (read history + create).

WS Agent skills write results via the ``save_review_result`` tool; REST uses
this service to list/get the history.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.employment_review import EmploymentReview
from app.repositories import employment_review_repo
from app.schemas.employment.review import EmploymentReviewCreate


class EmploymentReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_reviews(
        self,
        *,
        user_id: str,
        review_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EmploymentReview], int]:
        return employment_review_repo.list_by_user(
            self.db, user_id=user_id, review_type=review_type, skip=skip, limit=limit
        )

    def get_owned(self, review_id: str, *, user_id: str) -> EmploymentReview:
        review = employment_review_repo.get_by_id(self.db, review_id)
        if review is None or review.user_id != user_id:
            raise NotFoundError(message="Review not found", details={"id": review_id})
        return review

    def create(self, *, user_id: str, data: EmploymentReviewCreate) -> EmploymentReview:
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        review_type = fields.pop("review_type")
        return employment_review_repo.create(
            self.db, user_id=user_id, review_type=review_type, **fields
        )
