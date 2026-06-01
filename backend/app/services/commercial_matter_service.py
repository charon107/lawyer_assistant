"""Service layer for CommercialMatter.

A matter groups one counterparty relationship — the agreements reviewed,
the renewals registered, and the deviations logged against it. This service
owns matter CRUD and enforces per-user isolation (a user can only see /
mutate their own matters).

Repository calls never commit; the FastAPI session dependency owns commits.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.commercial_matter import CommercialMatter
from app.repositories import commercial_matter_repo
from app.schemas.commercial.matter import (
    CommercialMatterCreate,
    CommercialMatterUpdate,
)


class CommercialMatterService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_matter(self, user_id: str, data: CommercialMatterCreate) -> CommercialMatter:
        """Create a matter owned by `user_id`.

        Any `user_id` smuggled into the payload is dropped — we trust only
        the authenticated id passed as the first argument.
        """
        create_kwargs = data.model_dump(exclude_unset=True, exclude_none=True)
        create_kwargs.pop("user_id", None)
        return commercial_matter_repo.create(self.db, user_id=user_id, **create_kwargs)

    def get_my_matter(self, user_id: str, matter_id: str) -> CommercialMatter:
        """Return a single matter owned by `user_id`.

        Raises:
            NotFoundError: row doesn't exist.
            AuthorizationError: row exists but belongs to a different user.
        """
        matter = commercial_matter_repo.get_by_id(self.db, matter_id)
        if matter is None:
            raise NotFoundError(
                message="Commercial matter not found",
                details={"matter_id": matter_id},
            )
        if matter.user_id != user_id:
            raise AuthorizationError(message="You do not have access to this matter")
        return matter

    def list_my_matters(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CommercialMatter], int]:
        """Paginated list for the current user."""
        return commercial_matter_repo.list_by_user(self.db, user_id, skip=skip, limit=limit)

    def update_my_matter(
        self,
        user_id: str,
        matter_id: str,
        data: CommercialMatterUpdate,
    ) -> CommercialMatter:
        """Partial update of an owned matter."""
        matter = self.get_my_matter(user_id, matter_id)
        update_kwargs = data.model_dump(exclude_unset=True, exclude_none=True)
        update_kwargs.pop("user_id", None)
        return commercial_matter_repo.update(self.db, matter=matter, **update_kwargs)
