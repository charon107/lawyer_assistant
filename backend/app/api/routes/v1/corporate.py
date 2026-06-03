"""Corporate-legal (公司并购) module REST endpoints.

WebSocket (`/ws/corporate`) lives in `corporate_ws.py` and drives the
Agent skills (diligence / tabular / material-contract / deal-team-summary).

These REST endpoints cover module status, the practice profile, deal
(matter) CRUD, and read/write of the M&A-core child records. Agent-
produced records (diligence issues, tabular rows, material contracts) are
created via the WebSocket; the REST `create` paths here are for manual
entry and editing.
"""

from typing import Any

from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.api.deps import (
    BoardSvc,
    ClosingChecklistSvc,
    CorporateDealSvc,
    CorporateNotificationSvc,
    CorporateProfileSvc,
    CurrentUser,
    DiligenceSvc,
    EntityComplianceSvc,
    IntegrationSvc,
    MaterialContractSvc,
    TabularReviewSvc,
    VdrSvc,
)
from app.schemas.corporate.checklist import (
    ClosingChecklistItemCreate,
    ClosingChecklistItemList,
    ClosingChecklistItemRead,
    ClosingChecklistItemUpdate,
)
from app.schemas.corporate.deal import (
    CorporateDealCreate,
    CorporateDealList,
    CorporateDealRead,
    CorporateDealUpdate,
)
from app.schemas.corporate.diligence import (
    DiligenceIssueCreate,
    DiligenceIssueList,
    DiligenceIssueRead,
    DiligenceIssueUpdate,
)
from app.schemas.corporate.entity import (
    CorporateEntityCreate,
    CorporateEntityList,
    CorporateEntityRead,
    CorporateEntityUpdate,
    EntityComplianceItemCreate,
    EntityComplianceItemList,
    EntityComplianceItemRead,
    EntityComplianceItemUpdate,
)
from app.schemas.corporate.governance import (
    BoardDocumentCreate,
    BoardDocumentList,
    BoardDocumentRead,
    BoardDocumentUpdate,
    BoardMeetingCreate,
    BoardMeetingList,
    BoardMeetingRead,
)
from app.schemas.corporate.integration import (
    IntegrationTaskCreate,
    IntegrationTaskList,
    IntegrationTaskRead,
    IntegrationTaskUpdate,
)
from app.schemas.corporate.material_contract import (
    MaterialContractItemCreate,
    MaterialContractItemList,
    MaterialContractItemRead,
)
from app.schemas.corporate.notification import (
    CorporateNotificationList,
    CorporateNotificationRead,
)
from app.schemas.corporate.profile import (
    CorporateProfileCreate,
    CorporateProfileRead,
    CorporateProfileUpdate,
)
from app.schemas.corporate.tabular import TabularReviewList, TabularReviewRead
from app.schemas.corporate.vdr import (
    VdrDocumentCreate,
    VdrDocumentList,
    VdrDocumentRead,
)

router = APIRouter()


# --- module status + profile ------------------------------------------------


@router.get("/status")
def get_module_status(user: CurrentUser, profile_svc: CorporateProfileSvc) -> dict[str, Any]:
    """Whether the user has finished corporate-legal cold-start."""
    profile = profile_svc.get_my_profile_or_none(str(user.id))
    if profile is None:
        return {"configured": False, "setup_status": "not_started", "active_modules": None}
    import json

    modules = json.loads(profile.active_modules) if profile.active_modules else None
    return {
        "configured": profile.setup_status == "completed",
        "setup_status": profile.setup_status,
        "active_modules": modules,
    }


@router.post("/setup", response_model=CorporateProfileRead, status_code=status.HTTP_201_CREATED)
def cold_start_setup(
    data: CorporateProfileCreate, user: CurrentUser, profile_svc: CorporateProfileSvc
) -> Any:
    """Cold-start interview submission: upsert the profile and mark setup complete.

    Single-step setup — the frontend collects the selected modules
    (并购/董事会/公众公司/主体管理), the compiled `profile_content`, and the
    scalar fields, then posts them here.
    """
    profile_svc.upsert_my_profile(str(user.id), data)
    return profile_svc.upsert_my_profile(
        str(user.id), CorporateProfileUpdate(setup_status="completed")
    )


@router.get("/profile", response_model=CorporateProfileRead)
def get_profile(user: CurrentUser, profile_svc: CorporateProfileSvc) -> Any:
    return profile_svc.get_my_profile(str(user.id))


@router.put("/profile", response_model=CorporateProfileRead)
def update_profile(
    data: CorporateProfileUpdate, user: CurrentUser, profile_svc: CorporateProfileSvc
) -> Any:
    return profile_svc.upsert_my_profile(str(user.id), data)


# --- deals -------------------------------------------------------------------


@router.get("/deals", response_model=CorporateDealList)
def list_deals(
    user: CurrentUser,
    deal_svc: CorporateDealSvc,
    deal_status: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = deal_svc.list_deals(
        user_id=str(user.id), status=deal_status, skip=skip, limit=limit
    )
    return CorporateDealList(items=items, total=total)


@router.post("/deals", response_model=CorporateDealRead, status_code=status.HTTP_201_CREATED)
def create_deal(data: CorporateDealCreate, user: CurrentUser, deal_svc: CorporateDealSvc) -> Any:
    return deal_svc.create(user_id=str(user.id), data=data)


@router.get("/deals/{deal_id}", response_model=CorporateDealRead)
def get_deal(deal_id: str, user: CurrentUser, deal_svc: CorporateDealSvc) -> Any:
    return deal_svc.get_owned(deal_id, user_id=str(user.id))


@router.patch("/deals/{deal_id}", response_model=CorporateDealRead)
def update_deal(
    deal_id: str, data: CorporateDealUpdate, user: CurrentUser, deal_svc: CorporateDealSvc
) -> Any:
    return deal_svc.update(deal_id, user_id=str(user.id), data=data)


@router.post("/deals/{deal_id}/close", response_model=CorporateDealRead)
def close_deal(deal_id: str, user: CurrentUser, deal_svc: CorporateDealSvc) -> Any:
    return deal_svc.close(deal_id, user_id=str(user.id))


# --- VDR documents -----------------------------------------------------------


@router.get("/deals/{deal_id}/vdr", response_model=VdrDocumentList)
def list_vdr(
    deal_id: str,
    user: CurrentUser,
    vdr_svc: VdrSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    items, total = vdr_svc.list_for_deal(
        user_id=str(user.id), deal_id=deal_id, skip=skip, limit=limit
    )
    return VdrDocumentList(items=items, total=total)


@router.post(
    "/deals/{deal_id}/vdr", response_model=VdrDocumentRead, status_code=status.HTTP_201_CREATED
)
def create_vdr(deal_id: str, data: VdrDocumentCreate, user: CurrentUser, vdr_svc: VdrSvc) -> Any:
    # path deal_id is authoritative
    payload = data.model_copy(update={"deal_id": deal_id})
    return vdr_svc.create(user_id=str(user.id), data=payload)


@router.post(
    "/deals/{deal_id}/vdr/upload",
    response_model=VdrDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_vdr_file(
    deal_id: str,
    file: UploadFile = File(...),
    category: str | None = Form(None),
    priority: str = Form("normal"),
    user: CurrentUser = ...,
    vdr_svc: VdrSvc = ...,
) -> Any:
    """Upload a document to the deal's data room.

    Accepts PDF, DOCX, and text files. Content is parsed and stored
    so the AI agent can read it during diligence extraction.
    """
    file_data = await file.read()
    return vdr_svc.create_with_file(
        user_id=str(user.id),
        deal_id=deal_id,
        filename=file.filename or "unnamed",
        file_data=file_data,
        content_type=file.content_type,
        category=category,
        priority=priority,
    )


# --- diligence issues --------------------------------------------------------


@router.get("/deals/{deal_id}/diligence", response_model=DiligenceIssueList)
def list_diligence(
    deal_id: str,
    user: CurrentUser,
    diligence_svc: DiligenceSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    items, total = diligence_svc.list_for_deal(
        user_id=str(user.id), deal_id=deal_id, skip=skip, limit=limit
    )
    return DiligenceIssueList(items=items, total=total)


@router.post(
    "/deals/{deal_id}/diligence",
    response_model=DiligenceIssueRead,
    status_code=status.HTTP_201_CREATED,
)
def create_diligence(
    deal_id: str, data: DiligenceIssueCreate, user: CurrentUser, diligence_svc: DiligenceSvc
) -> Any:
    """Manually add a diligence finding (agent runs also create these via WS)."""
    payload = data.model_copy(update={"deal_id": deal_id})
    return diligence_svc.create(user_id=str(user.id), data=payload)


@router.patch("/diligence/{issue_id}", response_model=DiligenceIssueRead)
def update_diligence(
    issue_id: str, data: DiligenceIssueUpdate, user: CurrentUser, diligence_svc: DiligenceSvc
) -> Any:
    return diligence_svc.update(issue_id, user_id=str(user.id), data=data)


# --- closing checklist -------------------------------------------------------


@router.get("/deals/{deal_id}/checklist", response_model=ClosingChecklistItemList)
def list_checklist(
    deal_id: str,
    user: CurrentUser,
    checklist_svc: ClosingChecklistSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    items, total = checklist_svc.list_for_deal(
        user_id=str(user.id), deal_id=deal_id, skip=skip, limit=limit
    )
    return ClosingChecklistItemList(items=items, total=total)


@router.post(
    "/deals/{deal_id}/checklist",
    response_model=ClosingChecklistItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_checklist_item(
    deal_id: str,
    data: ClosingChecklistItemCreate,
    user: CurrentUser,
    checklist_svc: ClosingChecklistSvc,
) -> Any:
    payload = data.model_copy(update={"deal_id": deal_id})
    return checklist_svc.create(user_id=str(user.id), data=payload)


@router.patch("/checklist/{item_id}", response_model=ClosingChecklistItemRead)
def update_checklist_item(
    item_id: str,
    data: ClosingChecklistItemUpdate,
    user: CurrentUser,
    checklist_svc: ClosingChecklistSvc,
) -> Any:
    return checklist_svc.update(item_id, user_id=str(user.id), data=data)


# --- material contracts ------------------------------------------------------


@router.get("/deals/{deal_id}/material-contracts", response_model=MaterialContractItemList)
def list_material_contracts(
    deal_id: str,
    user: CurrentUser,
    material_svc: MaterialContractSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> Any:
    items, total = material_svc.list_for_deal(
        user_id=str(user.id), deal_id=deal_id, skip=skip, limit=limit
    )
    return MaterialContractItemList(items=items, total=total)


@router.post(
    "/deals/{deal_id}/material-contracts",
    response_model=MaterialContractItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_material_contract(
    deal_id: str,
    data: MaterialContractItemCreate,
    user: CurrentUser,
    material_svc: MaterialContractSvc,
) -> Any:
    payload = data.model_copy(update={"deal_id": deal_id})
    return material_svc.create(user_id=str(user.id), data=payload)


# --- tabular reviews ---------------------------------------------------------


@router.get("/deals/{deal_id}/tabular", response_model=TabularReviewList)
def list_tabular(
    deal_id: str,
    user: CurrentUser,
    tabular_svc: TabularReviewSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = tabular_svc.list_for_deal(
        user_id=str(user.id), deal_id=deal_id, skip=skip, limit=limit
    )
    return TabularReviewList(items=items, total=total)


@router.get("/tabular/{review_id}", response_model=TabularReviewRead)
def get_tabular(review_id: str, user: CurrentUser, tabular_svc: TabularReviewSvc) -> Any:
    return tabular_svc.get_owned(review_id, user_id=str(user.id))


# --- board governance --------------------------------------------------------


@router.get("/board/meetings", response_model=BoardMeetingList)
def list_board_meetings(user: CurrentUser, board_svc: BoardSvc) -> Any:
    items, total = board_svc.list_meetings(user_id=str(user.id))
    return BoardMeetingList(items=items, total=total)


@router.post(
    "/board/meetings", response_model=BoardMeetingRead, status_code=status.HTTP_201_CREATED
)
def create_board_meeting(data: BoardMeetingCreate, user: CurrentUser, board_svc: BoardSvc) -> Any:
    return board_svc.create_meeting(user_id=str(user.id), data=data)


@router.get("/board/documents", response_model=BoardDocumentList)
def list_board_documents(user: CurrentUser, board_svc: BoardSvc) -> Any:
    items, total = board_svc.list_documents(user_id=str(user.id))
    return BoardDocumentList(items=items, total=total)


@router.post(
    "/board/documents", response_model=BoardDocumentRead, status_code=status.HTTP_201_CREATED
)
def create_board_document(data: BoardDocumentCreate, user: CurrentUser, board_svc: BoardSvc) -> Any:
    return board_svc.create_document(user_id=str(user.id), data=data)


@router.patch("/board/documents/{doc_id}", response_model=BoardDocumentRead)
def update_board_document(
    doc_id: str, data: BoardDocumentUpdate, user: CurrentUser, board_svc: BoardSvc
) -> Any:
    return board_svc.update_document(doc_id, user_id=str(user.id), data=data)


# --- entities + compliance calendar ------------------------------------------


@router.get("/entities", response_model=CorporateEntityList)
def list_entities(user: CurrentUser, entity_svc: EntityComplianceSvc) -> Any:
    items, total = entity_svc.list_entities(user_id=str(user.id))
    return CorporateEntityList(items=items, total=total)


@router.post("/entities", response_model=CorporateEntityRead, status_code=status.HTTP_201_CREATED)
def create_entity(
    data: CorporateEntityCreate, user: CurrentUser, entity_svc: EntityComplianceSvc
) -> Any:
    return entity_svc.create_entity(user_id=str(user.id), data=data)


@router.patch("/entities/{entity_id}", response_model=CorporateEntityRead)
def update_entity(
    entity_id: str,
    data: CorporateEntityUpdate,
    user: CurrentUser,
    entity_svc: EntityComplianceSvc,
) -> Any:
    return entity_svc.update_entity(entity_id, user_id=str(user.id), data=data)


@router.get("/entities/{entity_id}/compliance", response_model=EntityComplianceItemList)
def list_entity_compliance(
    entity_id: str, user: CurrentUser, entity_svc: EntityComplianceSvc
) -> Any:
    items, total = entity_svc.list_compliance(entity_id, user_id=str(user.id))
    return EntityComplianceItemList(items=items, total=total)


@router.post(
    "/entities/{entity_id}/compliance",
    response_model=EntityComplianceItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_entity_compliance(
    entity_id: str,
    data: EntityComplianceItemCreate,
    user: CurrentUser,
    entity_svc: EntityComplianceSvc,
) -> Any:
    payload = data.model_copy(update={"entity_id": entity_id})
    return entity_svc.create_compliance(user_id=str(user.id), data=payload)


@router.patch("/compliance/{item_id}", response_model=EntityComplianceItemRead)
def update_entity_compliance(
    item_id: str,
    data: EntityComplianceItemUpdate,
    user: CurrentUser,
    entity_svc: EntityComplianceSvc,
) -> Any:
    return entity_svc.update_compliance(item_id, user_id=str(user.id), data=data)


# --- integration tasks -------------------------------------------------------


@router.get("/deals/{deal_id}/integration", response_model=IntegrationTaskList)
def list_integration(deal_id: str, user: CurrentUser, integration_svc: IntegrationSvc) -> Any:
    items, total = integration_svc.list_for_deal(user_id=str(user.id), deal_id=deal_id)
    return IntegrationTaskList(items=items, total=total)


@router.post(
    "/deals/{deal_id}/integration",
    response_model=IntegrationTaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_integration(
    deal_id: str, data: IntegrationTaskCreate, user: CurrentUser, integration_svc: IntegrationSvc
) -> Any:
    payload = data.model_copy(update={"deal_id": deal_id})
    return integration_svc.create(user_id=str(user.id), data=payload)


@router.patch("/integration/{task_id}", response_model=IntegrationTaskRead)
def update_integration(
    task_id: str, data: IntegrationTaskUpdate, user: CurrentUser, integration_svc: IntegrationSvc
) -> Any:
    return integration_svc.update(task_id, user_id=str(user.id), data=data)


# --- notifications -----------------------------------------------------------


@router.get("/notifications", response_model=CorporateNotificationList)
def list_notifications(user: CurrentUser, notif_svc: CorporateNotificationSvc) -> Any:
    items, total, unread = notif_svc.list_for_user(user_id=str(user.id))
    return CorporateNotificationList(items=items, total=total, unread=unread)


@router.post("/notifications/{notif_id}/read", response_model=CorporateNotificationRead)
def mark_notification_read(
    notif_id: str, user: CurrentUser, notif_svc: CorporateNotificationSvc
) -> Any:
    return notif_svc.mark_read(notif_id, user_id=str(user.id))
