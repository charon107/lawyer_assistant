"""IP-legal (知识产权) module REST endpoints.

WebSocket (`/ws/ip`) lives in `ip_ws.py` and drives the Agent skills
(clearance / fto / invention / infringement / ip_clause / oss / cease_desist /
takedown).

These REST endpoints cover module status, the 6-step cold-start wizard, the
practice profile (customize), enforcement-letter intake/management, the
portfolio register (CRUD + arithmetic report/audit), and read access to
Agent-produced reviews + notifications.
"""

from typing import Any

from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentUser,
    IpColdStartSvc,
    IpEnforcementSvc,
    IpNotificationSvc,
    IpPortfolioSvc,
    IpProfileSvc,
    IpReviewSvc,
)
from app.schemas.ip.cold_start import ColdStartRequest, ColdStartResponse
from app.schemas.ip.enforcement import (
    IpEnforcementCreate,
    IpEnforcementList,
    IpEnforcementRead,
    IpEnforcementUpdate,
)
from app.schemas.ip.notification import IpNotificationList, IpNotificationRead
from app.schemas.ip.portfolio import (
    IpPortfolioCreate,
    IpPortfolioList,
    IpPortfolioRead,
    IpPortfolioUpdate,
)
from app.schemas.ip.profile import (
    IpModuleStatusResponse,
    IpProfileRead,
    IpProfileUpdate,
)
from app.schemas.ip.review import IpReviewList, IpReviewRead

router = APIRouter()


# --- module status + cold-start + profile -----------------------------------


@router.get("/status", response_model=IpModuleStatusResponse)
def get_module_status(user: CurrentUser, profile_svc: IpProfileSvc) -> Any:
    """Whether the user has finished ip-legal cold-start."""
    profile = profile_svc.get_my_profile_or_none(str(user.id))
    if profile is None:
        return IpModuleStatusResponse(setup_status="not_started", configured=False)
    return IpModuleStatusResponse(
        setup_status=profile.setup_status,  # type: ignore[arg-type]
        configured=profile.setup_status == "completed",
    )


@router.post("/setup", response_model=ColdStartResponse)
def cold_start_setup(
    data: ColdStartRequest, user: CurrentUser, cold_start_svc: IpColdStartSvc
) -> Any:
    """Submit one step of the 6-step cold-start wizard."""
    return cold_start_svc.submit_step(str(user.id), data)


@router.get("/setup/status", response_model=ColdStartResponse)
def cold_start_status(user: CurrentUser, cold_start_svc: IpColdStartSvc) -> Any:
    """Where the user is in the cold-start wizard."""
    return cold_start_svc.get_progress(str(user.id))


@router.get("/profile", response_model=IpProfileRead)
def get_profile(user: CurrentUser, profile_svc: IpProfileSvc) -> Any:
    return profile_svc.get_my_profile(str(user.id))


@router.put("/profile", response_model=IpProfileRead)
def update_profile(data: IpProfileUpdate, user: CurrentUser, profile_svc: IpProfileSvc) -> Any:
    """Customize — update one or more aspects of the practice profile."""
    return profile_svc.upsert_my_profile(str(user.id), data)


# --- reviews (read history; written by WS agent) ----------------------------


@router.get("/reviews", response_model=IpReviewList)
def list_reviews(
    user: CurrentUser,
    review_svc: IpReviewSvc,
    review_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = review_svc.list_reviews(
        user_id=str(user.id), review_type=review_type, skip=skip, limit=limit
    )
    return IpReviewList(items=items, total=total)


@router.get("/reviews/{review_id}", response_model=IpReviewRead)
def get_review(review_id: str, user: CurrentUser, review_svc: IpReviewSvc) -> Any:
    return review_svc.get_owned(review_id, user_id=str(user.id))


# --- enforcement (intake + management; letters drafted via WS) --------------


@router.get("/enforcement", response_model=IpEnforcementList)
def list_enforcement(
    user: CurrentUser,
    enforcement_svc: IpEnforcementSvc,
    matter_type: str | None = Query(None),
    matter_status: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = enforcement_svc.list_enforcement(
        user_id=str(user.id),
        matter_type=matter_type,
        status=matter_status,
        skip=skip,
        limit=limit,
    )
    return IpEnforcementList(items=items, total=total)


@router.post("/enforcement", response_model=IpEnforcementRead, status_code=status.HTTP_201_CREATED)
def create_enforcement(
    data: IpEnforcementCreate, user: CurrentUser, enforcement_svc: IpEnforcementSvc
) -> Any:
    return enforcement_svc.create(user_id=str(user.id), data=data)


@router.get("/enforcement/{enforcement_id}", response_model=IpEnforcementRead)
def get_enforcement(
    enforcement_id: str, user: CurrentUser, enforcement_svc: IpEnforcementSvc
) -> Any:
    return enforcement_svc.get_owned(enforcement_id, user_id=str(user.id))


@router.put("/enforcement/{enforcement_id}", response_model=IpEnforcementRead)
def update_enforcement(
    enforcement_id: str,
    data: IpEnforcementUpdate,
    user: CurrentUser,
    enforcement_svc: IpEnforcementSvc,
) -> Any:
    return enforcement_svc.update(enforcement_id, user_id=str(user.id), data=data)


# --- portfolio (CRUD + arithmetic report/audit) -----------------------------


@router.get("/portfolio", response_model=IpPortfolioList)
def list_portfolio(
    user: CurrentUser,
    portfolio_svc: IpPortfolioSvc,
    asset_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> Any:
    items, total = portfolio_svc.list_assets(
        user_id=str(user.id), asset_type=asset_type, skip=skip, limit=limit
    )
    return IpPortfolioList(items=items, total=total)


@router.post("/portfolio", response_model=IpPortfolioRead, status_code=status.HTTP_201_CREATED)
def create_portfolio_asset(
    data: IpPortfolioCreate, user: CurrentUser, portfolio_svc: IpPortfolioSvc
) -> Any:
    return portfolio_svc.create(user_id=str(user.id), data=data)


@router.get("/portfolio/report")
def portfolio_report(user: CurrentUser, portfolio_svc: IpPortfolioSvc) -> Any:
    """Recompute deadlines + bucket by urgency (90-day window). Pure arithmetic."""
    return portfolio_svc.report(user_id=str(user.id))


@router.get("/portfolio/audit")
def portfolio_audit(user: CurrentUser, portfolio_svc: IpPortfolioSvc) -> Any:
    """Portfolio health check (撤三风险 / 长期 pending / 缺失关键日期) + deadline buckets."""
    return portfolio_svc.audit(user_id=str(user.id))


@router.put("/portfolio/{asset_id}", response_model=IpPortfolioRead)
def update_portfolio_asset(
    asset_id: str, data: IpPortfolioUpdate, user: CurrentUser, portfolio_svc: IpPortfolioSvc
) -> Any:
    return portfolio_svc.update(asset_id, user_id=str(user.id), data=data)


# --- notifications ----------------------------------------------------------


@router.get("/notifications", response_model=IpNotificationList)
def list_notifications(
    user: CurrentUser,
    notification_svc: IpNotificationSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = notification_svc.list_notifications(user_id=str(user.id), skip=skip, limit=limit)
    return IpNotificationList(items=items, total=total)


@router.post("/notifications/{notification_id}/read", response_model=IpNotificationRead)
def mark_notification_read(
    notification_id: str, user: CurrentUser, notification_svc: IpNotificationSvc
) -> Any:
    return notification_svc.mark_read(notification_id, user_id=str(user.id))
