"""Service layer for CorporateDeal (the deal / matter workspace).

Owns deal CRUD plus the ownership guard reused by the M&A-core child
services: a user may only touch deals they own, and child records are
always scoped through their parent deal.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.db.models.corporate_deal import CorporateDeal
from app.repositories import corporate_deal_repo
from app.schemas.corporate.deal import CorporateDealCreate, CorporateDealUpdate


class CorporateDealService:
    """Business logic for corporate-legal deals / matters."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, deal_id: str, *, user_id: str) -> CorporateDeal:
        """Return a deal the user owns, or raise NotFoundError.

        Reused by child services (VDR, diligence, etc.) to enforce that a
        caller can only reach records under their own deals — a missing or
        foreign deal is indistinguishable (no ownership leak).
        """
        deal = corporate_deal_repo.get_by_id(self.db, deal_id)
        if deal is None or deal.user_id != user_id:
            raise NotFoundError(message="Deal not found", details={"deal_id": deal_id})
        return deal

    def list_deals(
        self,
        *,
        user_id: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CorporateDeal], int]:
        return corporate_deal_repo.list_by_user(
            self.db, user_id=user_id, status=status, skip=skip, limit=limit
        )

    def create(self, *, user_id: str, data: CorporateDealCreate) -> CorporateDeal:
        existing = corporate_deal_repo.get_by_code(self.db, user_id=user_id, code=data.code)
        if existing is not None:
            raise AlreadyExistsError(
                message="A deal with this code already exists",
                details={"code": data.code},
            )
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        code = fields.pop("code")
        return corporate_deal_repo.create(self.db, user_id=user_id, code=code, **fields)

    def update(self, deal_id: str, *, user_id: str, data: CorporateDealUpdate) -> CorporateDeal:
        deal = self.get_owned(deal_id, user_id=user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        return corporate_deal_repo.update(self.db, deal=deal, **fields)

    def close(self, deal_id: str, *, user_id: str) -> CorporateDeal:
        deal = self.get_owned(deal_id, user_id=user_id)
        return corporate_deal_repo.update(self.db, deal=deal, status="closed")
