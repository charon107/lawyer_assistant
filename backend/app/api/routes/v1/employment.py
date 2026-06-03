"""Employment-legal (劳动用工) module REST endpoints.

WebSocket (`/ws/employment`) lives in `employment_ws.py` and drives the
Agent skills (hiring / termination / classification / policy / wage_hour /
handbook / expansion_analyze / investigation add·query·memo·summary).

These REST endpoints cover module status, the 6-step cold-start wizard, the
practice profile, and CRUD for leaves / investigations / expansions /
notifications. Agent-produced records (reviews, investigation log entries,
expansion analysis) are written via the WebSocket; REST create paths here are
for manual entry / management.
"""

from typing import Any

from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentUser,
    EmploymentColdStartSvc,
    EmploymentNotificationSvc,
    EmploymentProfileSvc,
    EmploymentReviewSvc,
    ExpansionSvc,
    InvestigationSvc,
    LeaveSvc,
)
from app.schemas.employment.cold_start import ColdStartRequest, ColdStartResponse
from app.schemas.employment.expansion import (
    ExpansionCreate,
    ExpansionList,
    ExpansionRead,
    ExpansionUpdate,
)
from app.schemas.employment.investigation import (
    InvestigationCreate,
    InvestigationDetail,
    InvestigationList,
    InvestigationRead,
    LogEntryCreate,
    LogEntryRead,
    SourceRead,
    SourceUpdate,
)
from app.schemas.employment.leave import (
    LeaveRegistrationCreate,
    LeaveRegistrationList,
    LeaveRegistrationRead,
    LeaveRegistrationUpdate,
)
from app.schemas.employment.notification import (
    EmploymentNotificationList,
    EmploymentNotificationRead,
)
from app.schemas.employment.profile import (
    EmploymentModuleStatusResponse,
    EmploymentProfileRead,
    EmploymentProfileUpdate,
)
from app.schemas.employment.review import EmploymentReviewList, EmploymentReviewRead

router = APIRouter()


# --- module status + cold-start + profile -----------------------------------


@router.get("/status", response_model=EmploymentModuleStatusResponse)
def get_module_status(user: CurrentUser, profile_svc: EmploymentProfileSvc) -> Any:
    """Whether the user has finished employment-legal cold-start."""
    profile = profile_svc.get_my_profile_or_none(str(user.id))
    if profile is None:
        return EmploymentModuleStatusResponse(setup_status="not_started", configured=False)
    return EmploymentModuleStatusResponse(
        setup_status=profile.setup_status,  # type: ignore[arg-type]
        configured=profile.setup_status == "completed",
    )


@router.post("/setup", response_model=ColdStartResponse)
def cold_start_setup(
    data: ColdStartRequest, user: CurrentUser, cold_start_svc: EmploymentColdStartSvc
) -> Any:
    """Submit one step of the 6-step cold-start wizard."""
    return cold_start_svc.submit_step(str(user.id), data)


@router.get("/setup/status", response_model=ColdStartResponse)
def cold_start_status(user: CurrentUser, cold_start_svc: EmploymentColdStartSvc) -> Any:
    """Where the user is in the cold-start wizard."""
    return cold_start_svc.get_progress(str(user.id))


@router.get("/profile", response_model=EmploymentProfileRead)
def get_profile(user: CurrentUser, profile_svc: EmploymentProfileSvc) -> Any:
    return profile_svc.get_my_profile(str(user.id))


@router.put("/profile", response_model=EmploymentProfileRead)
def update_profile(
    data: EmploymentProfileUpdate, user: CurrentUser, profile_svc: EmploymentProfileSvc
) -> Any:
    return profile_svc.upsert_my_profile(str(user.id), data)


# --- reviews (read history; written by WS agent) ----------------------------


@router.get("/reviews", response_model=EmploymentReviewList)
def list_reviews(
    user: CurrentUser,
    review_svc: EmploymentReviewSvc,
    review_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = review_svc.list_reviews(
        user_id=str(user.id), review_type=review_type, skip=skip, limit=limit
    )
    return EmploymentReviewList(items=items, total=total)


@router.get("/reviews/{review_id}", response_model=EmploymentReviewRead)
def get_review(review_id: str, user: CurrentUser, review_svc: EmploymentReviewSvc) -> Any:
    return review_svc.get_owned(review_id, user_id=str(user.id))


# --- leaves (log-leave + management) ----------------------------------------


@router.get("/leaves", response_model=LeaveRegistrationList)
def list_leaves(
    user: CurrentUser,
    leave_svc: LeaveSvc,
    leave_status: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = leave_svc.list_leaves(
        user_id=str(user.id), status=leave_status, skip=skip, limit=limit
    )
    return LeaveRegistrationList(items=items, total=total)


@router.post("/leaves", response_model=LeaveRegistrationRead, status_code=status.HTTP_201_CREATED)
def create_leave(data: LeaveRegistrationCreate, user: CurrentUser, leave_svc: LeaveSvc) -> Any:
    return leave_svc.create_leave(user_id=str(user.id), data=data)


@router.put("/leaves/{leave_id}", response_model=LeaveRegistrationRead)
def update_leave(
    leave_id: str, data: LeaveRegistrationUpdate, user: CurrentUser, leave_svc: LeaveSvc
) -> Any:
    return leave_svc.update_leave(leave_id, user_id=str(user.id), data=data)


# --- investigations ---------------------------------------------------------


@router.get("/investigations", response_model=InvestigationList)
def list_investigations(
    user: CurrentUser,
    inv_svc: InvestigationSvc,
    inv_status: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = inv_svc.list_investigations(
        user_id=str(user.id), status=inv_status, skip=skip, limit=limit
    )
    return InvestigationList(items=items, total=total)


@router.post(
    "/investigations", response_model=InvestigationRead, status_code=status.HTTP_201_CREATED
)
def open_investigation(
    data: InvestigationCreate, user: CurrentUser, inv_svc: InvestigationSvc
) -> Any:
    return inv_svc.open(user_id=str(user.id), data=data)


@router.get("/investigations/{investigation_id}", response_model=InvestigationDetail)
def get_investigation(investigation_id: str, user: CurrentUser, inv_svc: InvestigationSvc) -> Any:
    return inv_svc.get_owned(investigation_id, user_id=str(user.id))


@router.post(
    "/investigations/{investigation_id}/entries",
    response_model=LogEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def add_log_entry(
    investigation_id: str,
    data: LogEntryCreate,
    user: CurrentUser,
    inv_svc: InvestigationSvc,
) -> Any:
    return inv_svc.append_entry(investigation_id, user_id=str(user.id), data=data)


@router.put("/investigations/{investigation_id}/sources/{source_id}", response_model=SourceRead)
def update_source(
    investigation_id: str,
    source_id: str,
    data: SourceUpdate,
    user: CurrentUser,
    inv_svc: InvestigationSvc,
) -> Any:
    return inv_svc.update_source(source_id, user_id=str(user.id), data=data)


# --- expansions -------------------------------------------------------------


@router.get("/expansions", response_model=ExpansionList)
def list_expansions(
    user: CurrentUser,
    expansion_svc: ExpansionSvc,
    exp_status: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = expansion_svc.list_expansions(
        user_id=str(user.id), status=exp_status, skip=skip, limit=limit
    )
    return ExpansionList(items=items, total=total)


@router.post("/expansions", response_model=ExpansionRead, status_code=status.HTTP_201_CREATED)
def create_expansion(data: ExpansionCreate, user: CurrentUser, expansion_svc: ExpansionSvc) -> Any:
    return expansion_svc.create(user_id=str(user.id), data=data)


@router.put("/expansions/{expansion_id}", response_model=ExpansionRead)
def update_expansion(
    expansion_id: str, data: ExpansionUpdate, user: CurrentUser, expansion_svc: ExpansionSvc
) -> Any:
    return expansion_svc.update(expansion_id, user_id=str(user.id), data=data)


# --- notifications ----------------------------------------------------------


@router.get("/notifications", response_model=EmploymentNotificationList)
def list_notifications(
    user: CurrentUser,
    notification_svc: EmploymentNotificationSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = notification_svc.list_notifications(user_id=str(user.id), skip=skip, limit=limit)
    return EmploymentNotificationList(items=items, total=total)


@router.post("/notifications/{notification_id}/read", response_model=EmploymentNotificationRead)
def mark_notification_read(
    notification_id: str, user: CurrentUser, notification_svc: EmploymentNotificationSvc
) -> Any:
    return notification_svc.mark_read(notification_id, user_id=str(user.id))
