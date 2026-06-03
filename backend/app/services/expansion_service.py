"""Service layer for employment expansions.

expansion-kickoff (WS) pre-creates the row then the Agent fills the structure
analysis + tracking items; expansion-update (REST) edits tracking items.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.db.models.employment_expansion import EmploymentExpansion
from app.repositories import employment_expansion_repo
from app.schemas.employment.expansion import ExpansionCreate, ExpansionUpdate
from app.services._emp_serialize import dump_for_db

_JSON_FIELDS = {"position_types", "analysis_result", "tracking_items"}


class ExpansionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_expansions(
        self,
        *,
        user_id: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[EmploymentExpansion], int]:
        return employment_expansion_repo.list_by_user(
            self.db, user_id=user_id, status=status, skip=skip, limit=limit
        )

    def get_owned(self, expansion_id: str, *, user_id: str) -> EmploymentExpansion:
        exp = employment_expansion_repo.get_by_id(self.db, expansion_id)
        if exp is None or exp.user_id != user_id:
            raise NotFoundError(message="Expansion not found", details={"id": expansion_id})
        return exp

    def create(self, *, user_id: str, data: ExpansionCreate) -> EmploymentExpansion:
        existing = employment_expansion_repo.get_by_slug(self.db, user_id=user_id, slug=data.slug)
        if existing is not None:
            raise AlreadyExistsError(
                message="An expansion with this slug already exists",
                details={"slug": data.slug},
            )
        fields = dump_for_db(data, _JSON_FIELDS)
        slug = fields.pop("slug")
        province = fields.pop("province")
        return employment_expansion_repo.create(
            self.db, user_id=user_id, slug=slug, province=province, **fields
        )

    def update(
        self, expansion_id: str, *, user_id: str, data: ExpansionUpdate
    ) -> EmploymentExpansion:
        exp = self.get_owned(expansion_id, user_id=user_id)
        fields = dump_for_db(data, _JSON_FIELDS)
        return employment_expansion_repo.update(self.db, expansion=exp, **fields)
