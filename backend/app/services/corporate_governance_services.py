"""Services for the corporate-legal Phase 2 entities.

- BoardService           board meetings + governance documents (user-scoped)
- EntityComplianceService entity register + compliance calendar (user-scoped)
- IntegrationService     post-closing integration tasks (deal-scoped)
- CorporateNotificationService  in-app notifications (user-scoped)

Board / entity / notification records are owned directly by the user;
integration tasks hang off a deal and reuse the deal-ownership guard.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.board_meeting import BoardDocument, BoardMeeting
from app.db.models.corporate_entity import CorporateEntity, EntityComplianceItem
from app.db.models.corporate_notification import CorporateNotification
from app.db.models.integration_task import IntegrationTask
from app.repositories import (
    board_repo,
    corporate_entity_repo,
    corporate_notification_repo,
    integration_task_repo,
)
from app.schemas.corporate.entity import (
    CorporateEntityCreate,
    CorporateEntityUpdate,
    EntityComplianceItemCreate,
    EntityComplianceItemUpdate,
)
from app.schemas.corporate.governance import (
    BoardDocumentCreate,
    BoardDocumentUpdate,
    BoardMeetingCreate,
)
from app.schemas.corporate.integration import IntegrationTaskCreate, IntegrationTaskUpdate
from app.services.corporate_deal_service import CorporateDealService


class BoardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_meetings(self, *, user_id: str, skip: int = 0, limit: int = 100):
        return board_repo.list_meetings(self.db, user_id=user_id, skip=skip, limit=limit)

    def create_meeting(self, *, user_id: str, data: BoardMeetingCreate) -> BoardMeeting:
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        title = fields.pop("title")
        return board_repo.create_meeting(self.db, user_id=user_id, title=title, **fields)

    def list_documents(self, *, user_id: str, skip: int = 0, limit: int = 100):
        return board_repo.list_documents(self.db, user_id=user_id, skip=skip, limit=limit)

    def get_owned_document(self, doc_id: str, *, user_id: str) -> BoardDocument:
        row = board_repo.get_document(self.db, doc_id)
        if row is None or row.user_id != user_id:
            raise NotFoundError(message="Document not found", details={"id": doc_id})
        return row

    def create_document(self, *, user_id: str, data: BoardDocumentCreate) -> BoardDocument:
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        title = fields.pop("title")
        return board_repo.create_document(self.db, user_id=user_id, title=title, **fields)

    def update_document(
        self, doc_id: str, *, user_id: str, data: BoardDocumentUpdate
    ) -> BoardDocument:
        row = self.get_owned_document(doc_id, user_id=user_id)
        return board_repo.update_document(
            self.db, row=row, **data.model_dump(exclude_unset=True, exclude_none=True)
        )


class EntityComplianceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_entities(self, *, user_id: str, skip: int = 0, limit: int = 100):
        return corporate_entity_repo.list_entities(self.db, user_id=user_id, skip=skip, limit=limit)

    def get_owned_entity(self, entity_id: str, *, user_id: str) -> CorporateEntity:
        row = corporate_entity_repo.get_entity(self.db, entity_id)
        if row is None or row.user_id != user_id:
            raise NotFoundError(message="Entity not found", details={"id": entity_id})
        return row

    def create_entity(self, *, user_id: str, data: CorporateEntityCreate) -> CorporateEntity:
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        name = fields.pop("name")
        return corporate_entity_repo.create_entity(self.db, user_id=user_id, name=name, **fields)

    def update_entity(
        self, entity_id: str, *, user_id: str, data: CorporateEntityUpdate
    ) -> CorporateEntity:
        row = self.get_owned_entity(entity_id, user_id=user_id)
        return corporate_entity_repo.update_entity(
            self.db, row=row, **data.model_dump(exclude_unset=True, exclude_none=True)
        )

    def list_compliance(self, entity_id: str, *, user_id: str):
        self.get_owned_entity(entity_id, user_id=user_id)
        return corporate_entity_repo.list_compliance(self.db, entity_id=entity_id)

    def create_compliance(
        self, *, user_id: str, data: EntityComplianceItemCreate
    ) -> EntityComplianceItem:
        self.get_owned_entity(data.entity_id, user_id=user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        entity_id = fields.pop("entity_id")
        filing_type = fields.pop("filing_type")
        return corporate_entity_repo.create_compliance(
            self.db, entity_id=entity_id, filing_type=filing_type, **fields
        )

    def update_compliance(
        self, item_id: str, *, user_id: str, data: EntityComplianceItemUpdate
    ) -> EntityComplianceItem:
        row = corporate_entity_repo.get_compliance(self.db, item_id)
        if row is None:
            raise NotFoundError(message="Compliance item not found", details={"id": item_id})
        self.get_owned_entity(row.entity_id, user_id=user_id)
        return corporate_entity_repo.update_compliance(
            self.db, row=row, **data.model_dump(exclude_unset=True, exclude_none=True)
        )


class IntegrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._deals = CorporateDealService(db)

    def list_for_deal(self, *, user_id: str, deal_id: str):
        self._deals.get_owned(deal_id, user_id=user_id)
        return integration_task_repo.list_by_deal(self.db, deal_id=deal_id)

    def create(self, *, user_id: str, data: IntegrationTaskCreate) -> IntegrationTask:
        self._deals.get_owned(data.deal_id, user_id=user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        deal_id = fields.pop("deal_id")
        task = fields.pop("task")
        return integration_task_repo.create(self.db, deal_id=deal_id, task=task, **fields)

    def update(self, task_id: str, *, user_id: str, data: IntegrationTaskUpdate) -> IntegrationTask:
        row = integration_task_repo.get_by_id(self.db, task_id)
        if row is None:
            raise NotFoundError(message="Integration task not found", details={"id": task_id})
        self._deals.get_owned(row.deal_id, user_id=user_id)
        return integration_task_repo.update(
            self.db, row=row, **data.model_dump(exclude_unset=True, exclude_none=True)
        )


class CorporateNotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, *, user_id: str, skip: int = 0, limit: int = 50):
        items, total = corporate_notification_repo.list_by_user(
            self.db, user_id=user_id, skip=skip, limit=limit
        )
        unread = corporate_notification_repo.count_unread(self.db, user_id=user_id)
        return items, total, unread

    def mark_read(self, notif_id: str, *, user_id: str) -> CorporateNotification:
        row = corporate_notification_repo.get_by_id(self.db, notif_id)
        if row is None or row.user_id != user_id:
            raise NotFoundError(message="Notification not found", details={"id": notif_id})
        return corporate_notification_repo.mark_read(self.db, row=row)
