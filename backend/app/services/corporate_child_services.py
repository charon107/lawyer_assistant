"""Thin service layer for the M&A-core child entities of a deal.

VDR documents, diligence issues, closing-checklist items, material-contract
items, and tabular reviews are all scoped to a parent deal. Each service
routes every call through ``CorporateDealService.get_owned`` so a user can
only ever reach records under a deal they own (a missing or foreign deal
is indistinguishable — no ownership leak).

Grouped in one module because each is a small CRUD wrapper sharing the
same ownership guard; splitting into five near-identical files would add
files without adding clarity.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.closing_checklist_item import ClosingChecklistItem
from app.db.models.diligence_issue import DiligenceIssue
from app.db.models.material_contract_item import MaterialContractItem
from app.db.models.tabular_review import TabularReview
from app.db.models.vdr_document import VdrDocument
from app.repositories import (
    closing_checklist_repo,
    diligence_issue_repo,
    material_contract_repo,
    tabular_review_repo,
    vdr_document_repo,
)
from app.schemas.corporate.checklist import (
    ClosingChecklistItemCreate,
    ClosingChecklistItemUpdate,
)
from app.schemas.corporate.diligence import DiligenceIssueCreate, DiligenceIssueUpdate
from app.schemas.corporate.material_contract import (
    MaterialContractItemCreate,
    MaterialContractItemUpdate,
)
from app.schemas.corporate.vdr import VdrDocumentCreate, VdrDocumentUpdate
from app.services.corporate_deal_service import CorporateDealService


class _DealScoped:
    """Base: owns a db session + a deal-ownership guard."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._deals = CorporateDealService(db)

    def _ensure_owned(self, deal_id: str, *, user_id: str) -> None:
        self._deals.get_owned(deal_id, user_id=user_id)


class VdrService(_DealScoped):
    """Data-room document records under a deal."""

    def list_for_deal(
        self,
        *,
        user_id: str,
        deal_id: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[VdrDocument], int]:
        self._ensure_owned(deal_id, user_id=user_id)
        return vdr_document_repo.list_by_deal(
            self.db, deal_id=deal_id, status=status, skip=skip, limit=limit
        )

    def create(self, *, user_id: str, data: VdrDocumentCreate) -> VdrDocument:
        self._ensure_owned(data.deal_id, user_id=user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        deal_id = fields.pop("deal_id")
        filename = fields.pop("filename")
        return vdr_document_repo.create(self.db, deal_id=deal_id, filename=filename, **fields)

    def update(self, doc_id: str, *, user_id: str, data: VdrDocumentUpdate) -> VdrDocument:
        doc = vdr_document_repo.get_by_id(self.db, doc_id)
        if doc is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(message="VDR document not found", details={"id": doc_id})
        self._ensure_owned(doc.deal_id, user_id=user_id)
        return vdr_document_repo.update(
            self.db, doc=doc, **data.model_dump(exclude_unset=True, exclude_none=True)
        )


class DiligenceService(_DealScoped):
    """Diligence findings under a deal."""

    def list_for_deal(
        self,
        *,
        user_id: str,
        deal_id: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DiligenceIssue], int]:
        self._ensure_owned(deal_id, user_id=user_id)
        return diligence_issue_repo.list_by_deal(
            self.db, deal_id=deal_id, status=status, skip=skip, limit=limit
        )

    def create(self, *, user_id: str, data: DiligenceIssueCreate) -> DiligenceIssue:
        self._ensure_owned(data.deal_id, user_id=user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        deal_id = fields.pop("deal_id")
        title = fields.pop("title")
        return diligence_issue_repo.create(self.db, deal_id=deal_id, title=title, **fields)

    def update(self, issue_id: str, *, user_id: str, data: DiligenceIssueUpdate) -> DiligenceIssue:
        issue = diligence_issue_repo.get_by_id(self.db, issue_id)
        if issue is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(message="Diligence issue not found", details={"id": issue_id})
        self._ensure_owned(issue.deal_id, user_id=user_id)
        return diligence_issue_repo.update(
            self.db, issue=issue, **data.model_dump(exclude_unset=True, exclude_none=True)
        )


class ClosingChecklistService(_DealScoped):
    """Closing-checklist items under a deal."""

    def list_for_deal(
        self,
        *,
        user_id: str,
        deal_id: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[ClosingChecklistItem], int]:
        self._ensure_owned(deal_id, user_id=user_id)
        return closing_checklist_repo.list_by_deal(
            self.db, deal_id=deal_id, status=status, skip=skip, limit=limit
        )

    def create(self, *, user_id: str, data: ClosingChecklistItemCreate) -> ClosingChecklistItem:
        self._ensure_owned(data.deal_id, user_id=user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        deal_id = fields.pop("deal_id")
        item = fields.pop("item")
        return closing_checklist_repo.create(self.db, deal_id=deal_id, item=item, **fields)

    def update(
        self, item_id: str, *, user_id: str, data: ClosingChecklistItemUpdate
    ) -> ClosingChecklistItem:
        row = closing_checklist_repo.get_by_id(self.db, item_id)
        if row is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(message="Checklist item not found", details={"id": item_id})
        self._ensure_owned(row.deal_id, user_id=user_id)
        return closing_checklist_repo.update(
            self.db, row=row, **data.model_dump(exclude_unset=True, exclude_none=True)
        )


class MaterialContractService(_DealScoped):
    """Material-contract schedule items under a deal."""

    def list_for_deal(
        self, *, user_id: str, deal_id: str, skip: int = 0, limit: int = 100
    ) -> tuple[list[MaterialContractItem], int]:
        self._ensure_owned(deal_id, user_id=user_id)
        return material_contract_repo.list_by_deal(self.db, deal_id=deal_id, skip=skip, limit=limit)

    def create(self, *, user_id: str, data: MaterialContractItemCreate) -> MaterialContractItem:
        self._ensure_owned(data.deal_id, user_id=user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        deal_id = fields.pop("deal_id")
        contract = fields.pop("contract")
        return material_contract_repo.create(self.db, deal_id=deal_id, contract=contract, **fields)

    def update(
        self, item_id: str, *, user_id: str, data: MaterialContractItemUpdate
    ) -> MaterialContractItem:
        row = material_contract_repo.get_by_id(self.db, item_id)
        if row is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(message="Material contract item not found", details={"id": item_id})
        self._ensure_owned(row.deal_id, user_id=user_id)
        return material_contract_repo.update(
            self.db, row=row, **data.model_dump(exclude_unset=True, exclude_none=True)
        )


class TabularReviewService(_DealScoped):
    """Tabular-review jobs under a deal (creation/list; the agent fills rows)."""

    def list_for_deal(
        self, *, user_id: str, deal_id: str, skip: int = 0, limit: int = 50
    ) -> tuple[list[TabularReview], int]:
        self._ensure_owned(deal_id, user_id=user_id)
        return tabular_review_repo.list_by_deal(self.db, deal_id=deal_id, skip=skip, limit=limit)

    def get_owned(self, review_id: str, *, user_id: str) -> TabularReview:
        review = tabular_review_repo.get_by_id(self.db, review_id)
        if review is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError(message="Tabular review not found", details={"id": review_id})
        self._ensure_owned(review.deal_id, user_id=user_id)
        return review

    def create(
        self, *, user_id: str, deal_id: str, title: str, columns: object = None
    ) -> TabularReview:
        self._ensure_owned(deal_id, user_id=user_id)
        return tabular_review_repo.create(self.db, deal_id=deal_id, title=title, columns=columns)
