"""Litigation-legal (争议解决) module REST endpoints.

WebSocket (`/ws/litigation`) lives in `litigation_ws.py` and drives the Agent
skills (matter_briefing / demand_draft / demand_received / subpoena_triage /
legal_hold / chronology / claim_chart / oc_status / brief_section /
deposition_prep / privilege_log).

These REST endpoints cover module status, the 5-step cold-start wizard, the
practice profile (customize), matter CRUD + close + portfolio, matter events,
demand intake/management, analysis history read, and notifications.
"""

from typing import Any

from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentUser,
    LitigationAnalysisSvc,
    LitigationColdStartSvc,
    LitigationDemandSvc,
    LitigationMatterSvc,
    LitigationNotificationSvc,
    LitigationProfileSvc,
)
from app.schemas.litigation.analysis import LitigationAnalysisList, LitigationAnalysisRead
from app.schemas.litigation.cold_start import ColdStartRequest, ColdStartResponse
from app.schemas.litigation.demand import (
    LitigationDemandCreate,
    LitigationDemandList,
    LitigationDemandRead,
    LitigationDemandUpdate,
)
from app.schemas.litigation.matter import (
    LitigationMatterCreate,
    LitigationMatterList,
    LitigationMatterRead,
    LitigationMatterUpdate,
)
from app.schemas.litigation.matter_event import (
    LitigationMatterEventCreate,
    LitigationMatterEventList,
    LitigationMatterEventRead,
)
from app.schemas.litigation.notification import (
    LitigationNotificationList,
    LitigationNotificationRead,
)
from app.schemas.litigation.profile import (
    LitigationModuleStatusResponse,
    LitigationProfileRead,
    LitigationProfileUpdate,
)

router = APIRouter()


# --- module status + cold-start + profile -----------------------------------


@router.get("/status", response_model=LitigationModuleStatusResponse)
def get_module_status(user: CurrentUser, profile_svc: LitigationProfileSvc) -> Any:
    """Whether the user has finished litigation-legal cold-start."""
    profile = profile_svc.get_my_profile_or_none(str(user.id))
    if profile is None:
        return LitigationModuleStatusResponse(setup_status="not_started", configured=False)
    return LitigationModuleStatusResponse(
        setup_status=profile.setup_status,  # type: ignore[arg-type]
        configured=profile.setup_status == "completed",
    )


@router.post("/setup", response_model=ColdStartResponse)
def cold_start_setup(
    data: ColdStartRequest, user: CurrentUser, cold_start_svc: LitigationColdStartSvc
) -> Any:
    """Submit one step of the 5-step cold-start wizard."""
    return cold_start_svc.submit_step(str(user.id), data)


@router.get("/setup/status", response_model=ColdStartResponse)
def cold_start_status(user: CurrentUser, cold_start_svc: LitigationColdStartSvc) -> Any:
    """Where the user is in the cold-start wizard."""
    return cold_start_svc.get_progress(str(user.id))


@router.get("/profile", response_model=LitigationProfileRead)
def get_profile(user: CurrentUser, profile_svc: LitigationProfileSvc) -> Any:
    return profile_svc.get_my_profile(str(user.id))


@router.put("/profile", response_model=LitigationProfileRead)
def update_profile(
    data: LitigationProfileUpdate, user: CurrentUser, profile_svc: LitigationProfileSvc
) -> Any:
    """Customize — update one or more aspects of the practice profile."""
    return profile_svc.upsert_my_profile(str(user.id), data)


# --- matters CRUD + close + portfolio + events ------------------------------


@router.get("/matters", response_model=LitigationMatterList)
def list_matters(
    user: CurrentUser,
    matter_svc: LitigationMatterSvc,
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = matter_svc.list_matters(
        user_id=str(user.id), status=status_filter, skip=skip, limit=limit
    )
    return LitigationMatterList(items=items, total=total)


@router.post("/matters", response_model=LitigationMatterRead, status_code=status.HTTP_201_CREATED)
def create_matter(
    data: LitigationMatterCreate, user: CurrentUser, matter_svc: LitigationMatterSvc
) -> Any:
    """Register a new litigation matter（含冲突门禁）。"""
    return matter_svc.create(user_id=str(user.id), data=data)


@router.get("/matters/portfolio")
def portfolio_status(user: CurrentUser, matter_svc: LitigationMatterSvc) -> Any:
    """案件组合概览 — 聚合算术：风险分布 / 期限 / 陈旧 / 7 类异常。"""
    return matter_svc.portfolio(str(user.id))


@router.get("/matters/{matter_id}", response_model=LitigationMatterRead)
def get_matter(matter_id: str, user: CurrentUser, matter_svc: LitigationMatterSvc) -> Any:
    return matter_svc.get_owned(matter_id, user_id=str(user.id))


@router.put("/matters/{matter_id}", response_model=LitigationMatterRead)
def update_matter(
    matter_id: str, data: LitigationMatterUpdate, user: CurrentUser, matter_svc: LitigationMatterSvc
) -> Any:
    """Update matter fields + 追加事件流。"""
    return matter_svc.update(matter_id, user_id=str(user.id), data=data)


@router.post("/matters/{matter_id}/close", response_model=LitigationMatterRead)
def close_matter(matter_id: str, user: CurrentUser, matter_svc: LitigationMatterSvc) -> Any:
    """Close a matter（非律师门禁审查）。"""
    return matter_svc.close(matter_id, user_id=str(user.id))


# --- matter events ---------------------------------------------------------


@router.get("/matters/{matter_id}/events", response_model=LitigationMatterEventList)
def list_matter_events(
    matter_id: str,
    user: CurrentUser,
    matter_svc: LitigationMatterSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
) -> Any:
    events = matter_svc.list_events(
        matter_id=matter_id, user_id=str(user.id), skip=skip, limit=limit
    )
    return LitigationMatterEventList(
        items=events,
        total=len(events),  # events from list_by_matter is full list
    )


@router.post(
    "/matters/{matter_id}/events",
    response_model=LitigationMatterEventRead,
    status_code=status.HTTP_201_CREATED,
)
def create_matter_event(
    matter_id: str,
    data: LitigationMatterEventCreate,
    user: CurrentUser,
    matter_svc: LitigationMatterSvc,
) -> Any:
    """Add an event to a matter's timeline."""
    return matter_svc.add_event(matter_id=matter_id, user_id=str(user.id), data=data)


# --- demands ----------------------------------------------------------------


@router.get("/demands", response_model=LitigationDemandList)
def list_demands(
    user: CurrentUser,
    demand_svc: LitigationDemandSvc,
    mode: str | None = Query(None),
    demand_status: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = demand_svc.list_demands(
        user_id=str(user.id), mode=mode, status=demand_status, skip=skip, limit=limit
    )
    return LitigationDemandList(items=items, total=total)


@router.post("/demands", response_model=LitigationDemandRead, status_code=status.HTTP_201_CREATED)
def create_demand(
    data: LitigationDemandCreate, user: CurrentUser, demand_svc: LitigationDemandSvc
) -> Any:
    """Create a demand letter matter (发送 or 接收模式)。"""
    return demand_svc.create(user_id=str(user.id), data=data)


@router.get("/demands/{demand_id}", response_model=LitigationDemandRead)
def get_demand(demand_id: str, user: CurrentUser, demand_svc: LitigationDemandSvc) -> Any:
    return demand_svc.get_owned(demand_id, user_id=str(user.id))


@router.put("/demands/{demand_id}", response_model=LitigationDemandRead)
def update_demand(
    demand_id: str,
    data: LitigationDemandUpdate,
    user: CurrentUser,
    demand_svc: LitigationDemandSvc,
) -> Any:
    return demand_svc.update(demand_id, user_id=str(user.id), data=data)


# --- analyses (read history; written by WS agent) ---------------------------


@router.get("/analyses", response_model=LitigationAnalysisList)
def list_analyses(
    user: CurrentUser,
    analysis_svc: LitigationAnalysisSvc,
    analysis_type: str | None = Query(None),
    matter_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = analysis_svc.list_analyses(
        user_id=str(user.id),
        analysis_type=analysis_type,
        matter_id=matter_id,
        skip=skip,
        limit=limit,
    )
    return LitigationAnalysisList(items=items, total=total)


@router.get("/analyses/{analysis_id}", response_model=LitigationAnalysisRead)
def get_analysis(analysis_id: str, user: CurrentUser, analysis_svc: LitigationAnalysisSvc) -> Any:
    return analysis_svc.get_owned(analysis_id, user_id=str(user.id))


# --- notifications ----------------------------------------------------------


@router.get("/notifications", response_model=LitigationNotificationList)
def list_notifications(
    user: CurrentUser,
    notification_svc: LitigationNotificationSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = notification_svc.list_notifications(user_id=str(user.id), skip=skip, limit=limit)
    return LitigationNotificationList(items=items, total=total)


@router.post("/notifications/{notification_id}/read", response_model=LitigationNotificationRead)
def mark_notification_read(
    notification_id: str, user: CurrentUser, notification_svc: LitigationNotificationSvc
) -> Any:
    return notification_svc.mark_read(notification_id, user_id=str(user.id))
