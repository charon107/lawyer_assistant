"""Service layer for ContractReview.

Owns the lifecycle of a contract-review row:
- Pre-create an in-progress shell before the WS handler kicks off
  the agent.
- Look up history for the `/reviews` endpoints.
- Enforce per-user isolation (a user can only see / mutate their own
  reviews).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.contract_review import ContractReview
from app.repositories import contract_review_repo
from app.schemas.commercial.review import ContractReviewCreate


class ContractReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def start_review(
        self,
        user_id: str,
        data: ContractReviewCreate,
    ) -> ContractReview:
        """Create an `in_progress` review row.

        The WS handler reads the returned id, drops it into
        CommercialDeps.review_id, and runs the agent. The agent's
        final `write_contract_review` tool call updates the row to
        completed.
        """
        return contract_review_repo.create(
            self.db,
            user_id=user_id,
            review_type=data.review_type,
            counterparty=data.counterparty,
            agreement_name=data.agreement_name,
            agreement_type=data.agreement_type,
            side=data.side,
            annual_value=data.annual_value,
            file_path=data.file_path,
            file_name=data.file_name,
            matter_id=data.matter_id,
        )

    def get_my_review(self, user_id: str, review_id: str) -> ContractReview:
        """Return a single review owned by `user_id`.

        Raises:
            NotFoundError: row doesn't exist.
            AuthorizationError: row exists but belongs to a different user.
        """
        review = contract_review_repo.get_by_id(self.db, review_id)
        if review is None:
            raise NotFoundError(
                message="Contract review not found",
                details={"review_id": review_id},
            )
        if review.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this contract review",
            )
        return review

    def list_my_reviews(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ContractReview], int]:
        """Paginated history for the current user."""
        return contract_review_repo.list_by_user(
            self.db,
            user_id=user_id,
            skip=skip,
            limit=limit,
        )
