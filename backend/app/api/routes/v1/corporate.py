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

from fastapi import APIRouter, Query, status

from app.api.deps import (
    ClosingChecklistSvc,
    CorporateDealSvc,
    CorporateProfileSvc,
    CurrentUser,
    DiligenceSvc,
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
    DiligenceIssueList,
    DiligenceIssueRead,
    DiligenceIssueUpdate,
)
from app.schemas.corporate.material_contract import (
    MaterialContractItemCreate,
    MaterialContractItemList,
    MaterialContractItemRead,
)
from app.schemas.corporate.profile import (
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
