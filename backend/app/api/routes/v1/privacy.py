"""Privacy-legal (个人信息保护) module REST endpoints.

WebSocket (`/ws/privacy`) lives in `privacy_ws.py` and drives the Agent
skills (triage / dpa / pia / gap / dsar / policy_sweep / policy_query).

These REST endpoints cover module status, the 6-step cold-start wizard, the
practice profile (customize), DSAR intake/management, and read access to
Agent-produced reviews + notifications.
"""

from typing import Any

from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentUser,
    PrivacyColdStartSvc,
    PrivacyDsarSvc,
    PrivacyNotificationSvc,
    PrivacyProfileSvc,
    PrivacyReviewSvc,
)
from app.schemas.privacy.cold_start import ColdStartRequest, ColdStartResponse
from app.schemas.privacy.dsar import (
    PrivacyDsarCreate,
    PrivacyDsarList,
    PrivacyDsarRead,
    PrivacyDsarUpdate,
)
from app.schemas.privacy.notification import (
    PrivacyNotificationList,
    PrivacyNotificationRead,
)
from app.schemas.privacy.profile import (
    PrivacyModuleStatusResponse,
    PrivacyProfileRead,
    PrivacyProfileUpdate,
)
from app.schemas.privacy.review import PrivacyReviewList, PrivacyReviewRead

router = APIRouter()


# --- module status + cold-start + profile -----------------------------------


@router.get("/status", response_model=PrivacyModuleStatusResponse)
def get_module_status(user: CurrentUser, profile_svc: PrivacyProfileSvc) -> Any:
    """Whether the user has finished privacy-legal cold-start."""
    profile = profile_svc.get_my_profile_or_none(str(user.id))
    if profile is None:
        return PrivacyModuleStatusResponse(setup_status="not_started", configured=False)
    return PrivacyModuleStatusResponse(
        setup_status=profile.setup_status,  # type: ignore[arg-type]
        configured=profile.setup_status == "completed",
    )


@router.post("/setup", response_model=ColdStartResponse)
def cold_start_setup(
    data: ColdStartRequest, user: CurrentUser, cold_start_svc: PrivacyColdStartSvc
) -> Any:
    """Submit one step of the 6-step cold-start wizard."""
    return cold_start_svc.submit_step(str(user.id), data)


@router.get("/setup/status", response_model=ColdStartResponse)
def cold_start_status(user: CurrentUser, cold_start_svc: PrivacyColdStartSvc) -> Any:
    """Where the user is in the cold-start wizard."""
    return cold_start_svc.get_progress(str(user.id))


@router.get("/profile", response_model=PrivacyProfileRead)
def get_profile(user: CurrentUser, profile_svc: PrivacyProfileSvc) -> Any:
    return profile_svc.get_my_profile(str(user.id))


@router.put("/profile", response_model=PrivacyProfileRead)
def update_profile(
    data: PrivacyProfileUpdate, user: CurrentUser, profile_svc: PrivacyProfileSvc
) -> Any:
    """Customize — update one or more aspects of the practice profile."""
    return profile_svc.upsert_my_profile(str(user.id), data)


# --- reviews (read history; written by WS agent) ----------------------------


@router.get("/reviews", response_model=PrivacyReviewList)
def list_reviews(
    user: CurrentUser,
    review_svc: PrivacyReviewSvc,
    review_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = review_svc.list_reviews(
        user_id=str(user.id), review_type=review_type, skip=skip, limit=limit
    )
    return PrivacyReviewList(items=items, total=total)


@router.get("/reviews/{review_id}", response_model=PrivacyReviewRead)
def get_review(review_id: str, user: CurrentUser, review_svc: PrivacyReviewSvc) -> Any:
    return review_svc.get_owned(review_id, user_id=str(user.id))


# --- DSAR (intake + management; two letters drafted via WS) ------------------


@router.get("/dsar", response_model=PrivacyDsarList)
def list_dsar(
    user: CurrentUser,
    dsar_svc: PrivacyDsarSvc,
    dsar_status: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = dsar_svc.list_dsar(
        user_id=str(user.id), status=dsar_status, skip=skip, limit=limit
    )
    return PrivacyDsarList(items=items, total=total)


@router.post("/dsar", response_model=PrivacyDsarRead, status_code=status.HTTP_201_CREATED)
def create_dsar(data: PrivacyDsarCreate, user: CurrentUser, dsar_svc: PrivacyDsarSvc) -> Any:
    return dsar_svc.create(user_id=str(user.id), data=data)


@router.get("/dsar/{dsar_id}", response_model=PrivacyDsarRead)
def get_dsar(dsar_id: str, user: CurrentUser, dsar_svc: PrivacyDsarSvc) -> Any:
    return dsar_svc.get_owned(dsar_id, user_id=str(user.id))


@router.put("/dsar/{dsar_id}", response_model=PrivacyDsarRead)
def update_dsar(
    dsar_id: str, data: PrivacyDsarUpdate, user: CurrentUser, dsar_svc: PrivacyDsarSvc
) -> Any:
    return dsar_svc.update(dsar_id, user_id=str(user.id), data=data)


# --- notifications ----------------------------------------------------------


@router.get("/notifications", response_model=PrivacyNotificationList)
def list_notifications(
    user: CurrentUser,
    notification_svc: PrivacyNotificationSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = notification_svc.list_notifications(user_id=str(user.id), skip=skip, limit=limit)
    return PrivacyNotificationList(items=items, total=total)


@router.post("/notifications/{notification_id}/read", response_model=PrivacyNotificationRead)
def mark_notification_read(
    notification_id: str, user: CurrentUser, notification_svc: PrivacyNotificationSvc
) -> Any:
    return notification_svc.mark_read(notification_id, user_id=str(user.id))
