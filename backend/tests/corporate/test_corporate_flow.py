"""End-to-end-ish service tests for the corporate-legal module.

Exercises the deal anchor + child services + Phase 2 services + the
dataroom-watcher, all against a real in-memory schema.
"""

import uuid

import pytest

from app.core.exceptions import NotFoundError
from app.schemas.corporate.deal import CorporateDealCreate
from app.schemas.corporate.diligence import DiligenceIssueCreate
from app.schemas.corporate.entity import (
    CorporateEntityCreate,
    EntityComplianceItemCreate,
)
from app.schemas.corporate.governance import BoardDocumentCreate
from app.schemas.corporate.integration import IntegrationTaskCreate
from app.schemas.corporate.vdr import VdrDocumentCreate
from app.services.corporate_child_services import DiligenceService, VdrService
from app.services.corporate_deal_service import CorporateDealService
from app.services.corporate_governance_services import (
    BoardService,
    EntityComplianceService,
    IntegrationService,
)


def _other_user(db) -> str:
    from app.db.models.user import User

    uid = str(uuid.uuid4())
    db.add(User(id=uid, email=f"{uid[:8]}@test.local", hashed_password="x" * 60, is_active=True))
    db.flush()
    return uid


class TestDealService:
    def test_create_and_list(self, db, user_id):
        svc = CorporateDealService(db)
        deal = svc.create(user_id=user_id, data=CorporateDealCreate(code="acme-2026", side="buyer"))
        assert deal.id and deal.code == "acme-2026"
        items, total = svc.list_deals(user_id=user_id)
        assert total == 1 and items[0].id == deal.id

    def test_duplicate_code_rejected(self, db, user_id):
        svc = CorporateDealService(db)
        svc.create(user_id=user_id, data=CorporateDealCreate(code="dup"))
        from app.core.exceptions import AlreadyExistsError

        with pytest.raises(AlreadyExistsError):
            svc.create(user_id=user_id, data=CorporateDealCreate(code="dup"))

    def test_get_owned_rejects_foreign_user(self, db, user_id):
        svc = CorporateDealService(db)
        deal = svc.create(user_id=user_id, data=CorporateDealCreate(code="x"))
        other = _other_user(db)
        with pytest.raises(NotFoundError):
            svc.get_owned(deal.id, user_id=other)


class TestChildServicesOwnership:
    def test_vdr_and_diligence_scoped_to_owner(self, db, user_id):
        deal = CorporateDealService(db).create(user_id=user_id, data=CorporateDealCreate(code="d1"))
        vdr = VdrService(db)
        vdr.create(user_id=user_id, data=VdrDocumentCreate(deal_id=deal.id, filename="msa.pdf"))
        docs, total = vdr.list_for_deal(user_id=user_id, deal_id=deal.id)
        assert total == 1 and docs[0].filename == "msa.pdf"

        dil = DiligenceService(db)
        dil.create(
            user_id=user_id,
            data=DiligenceIssueCreate(deal_id=deal.id, title="控制权变更", severity="blocking"),
        )
        issues, n = dil.list_for_deal(user_id=user_id, deal_id=deal.id)
        assert n == 1 and issues[0].severity == "blocking"

        other = _other_user(db)
        with pytest.raises(NotFoundError):
            vdr.list_for_deal(user_id=other, deal_id=deal.id)


class TestPhase2Services:
    def test_board_document(self, db, user_id):
        svc = BoardService(db)
        doc = svc.create_document(
            user_id=user_id,
            data=BoardDocumentCreate(title="股东会决议", doc_kind="written_consent", content="..."),
        )
        assert doc.id
        got = svc.get_owned_document(doc.id, user_id=user_id)
        assert got.doc_kind == "written_consent"

    def test_entity_compliance(self, db, user_id):
        svc = EntityComplianceService(db)
        ent = svc.create_entity(user_id=user_id, data=CorporateEntityCreate(name="子公司A"))
        svc.create_compliance(
            user_id=user_id,
            data=EntityComplianceItemCreate(entity_id=ent.id, filing_type="年度报告"),
        )
        items, total = svc.list_compliance(ent.id, user_id=user_id)
        assert total == 1 and items[0].filing_type == "年度报告"

    def test_integration_task(self, db, user_id):
        deal = CorporateDealService(db).create(
            user_id=user_id, data=CorporateDealCreate(code="int-1")
        )
        svc = IntegrationService(db)
        svc.create(
            user_id=user_id,
            data=IntegrationTaskCreate(deal_id=deal.id, task="公章交接", phase="D1"),
        )
        items, total = svc.list_for_deal(user_id=user_id, deal_id=deal.id)
        assert total == 1 and items[0].phase == "D1"


class TestDataroomWatcher:
    def test_writes_notification_for_new_docs(self, db, user_id):
        from app.tasks import dataroom_watcher

        deal = CorporateDealService(db).create(
            user_id=user_id, data=CorporateDealCreate(code="dr-1")
        )
        VdrService(db).create(
            user_id=user_id,
            data=VdrDocumentCreate(
                deal_id=deal.id, filename="重大合同-1.pdf", category="重大合同", priority="high"
            ),
        )
        written = dataroom_watcher.run(db)
        assert written == 1
        from app.repositories import corporate_notification_repo

        items, total = corporate_notification_repo.list_by_user(db, user_id=user_id)
        assert total == 1 and "dr-1" in items[0].title
