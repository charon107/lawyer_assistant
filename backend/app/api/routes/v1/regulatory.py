"""Regulatory-legal (监管合规) module REST endpoints.

WebSocket (`/ws/regulatory`) lives in `regulatory_ws.py` and drives the Agent
skills (reg_feed_watch / policy_diff / policy_redraft).

These REST endpoints cover module status, the 6-step cold-start wizard, the
practice profile (customize), reg-item list + manual entry, analysis history
read, the gap tracker (status report + close + risk-accept), the comment-period
tracker (decision), and notifications. All CRUD / aggregation arithmetic — no LLM.
"""

from typing import Any

from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentUser,
    RegulatoryAnalysisSvc,
    RegulatoryColdStartSvc,
    RegulatoryCommentSvc,
    RegulatoryGapSvc,
    RegulatoryNotificationSvc,
    RegulatoryProfileSvc,
    RegulatoryRegItemSvc,
)
from app.schemas.regulatory.analysis import RegulatoryAnalysisList, RegulatoryAnalysisRead
from app.schemas.regulatory.cold_start import ColdStartRequest, ColdStartResponse
from app.schemas.regulatory.comment import (
    RegulatoryCommentDecide,
    RegulatoryCommentList,
    RegulatoryCommentRead,
)
from app.schemas.regulatory.gap import (
    RegulatoryGapAccept,
    RegulatoryGapClose,
    RegulatoryGapCreate,
    RegulatoryGapRead,
    RegulatoryGapStatusReport,
    RegulatoryGapUpdate,
)
from app.schemas.regulatory.notification import (
    RegulatoryNotificationList,
    RegulatoryNotificationRead,
)
from app.schemas.regulatory.profile import (
    RegulatoryModuleStatusResponse,
    RegulatoryProfileRead,
    RegulatoryProfileUpdate,
)
from app.schemas.regulatory.reg_item import (
    RegulatoryRegItemCreate,
    RegulatoryRegItemList,
    RegulatoryRegItemRead,
    RegulatoryRegItemUpdate,
)

router = APIRouter()


# --- module status + cold-start + profile -----------------------------------


@router.get("/status", response_model=RegulatoryModuleStatusResponse)
def get_module_status(user: CurrentUser, profile_svc: RegulatoryProfileSvc) -> Any:
    """Whether the user has finished regulatory-legal cold-start."""
    profile = profile_svc.get_my_profile_or_none(str(user.id))
    if profile is None:
        return RegulatoryModuleStatusResponse(setup_status="not_started", configured=False)
    return RegulatoryModuleStatusResponse(
        setup_status=profile.setup_status,  # type: ignore[arg-type]
        configured=profile.setup_status == "completed",
    )


@router.post("/setup", response_model=ColdStartResponse)
def cold_start_setup(
    data: ColdStartRequest, user: CurrentUser, cold_start_svc: RegulatoryColdStartSvc
) -> Any:
    """Submit one step of the 6-step cold-start wizard."""
    return cold_start_svc.submit_step(str(user.id), data)


@router.get("/setup/status", response_model=ColdStartResponse)
def cold_start_status(user: CurrentUser, cold_start_svc: RegulatoryColdStartSvc) -> Any:
    """Where the user is in the cold-start wizard."""
    return cold_start_svc.get_progress(str(user.id))


@router.get("/profile", response_model=RegulatoryProfileRead)
def get_profile(user: CurrentUser, profile_svc: RegulatoryProfileSvc) -> Any:
    return profile_svc.get_my_profile(str(user.id))


@router.put("/profile", response_model=RegulatoryProfileRead)
def update_profile(
    data: RegulatoryProfileUpdate, user: CurrentUser, profile_svc: RegulatoryProfileSvc
) -> Any:
    """Customize — update monitoring watchlist / policy library / thresholds / feed config."""
    return profile_svc.upsert_my_profile(str(user.id), data)


# --- reg items (list + manual paste entry) ----------------------------------


@router.get("/items", response_model=RegulatoryRegItemList)
def list_items(
    user: CurrentUser,
    reg_item_svc: RegulatoryRegItemSvc,
    materiality: str | None = Query(None),
    item_type: str | None = Query(None),
    item_status: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = reg_item_svc.list_items(
        user_id=str(user.id),
        materiality=materiality,
        item_type=item_type,
        status=item_status,
        skip=skip,
        limit=limit,
    )
    return RegulatoryRegItemList(items=items, total=total)


@router.post("/items", response_model=RegulatoryRegItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    data: RegulatoryRegItemCreate, user: CurrentUser, reg_item_svc: RegulatoryRegItemSvc
) -> Any:
    """手动粘贴录入法规文本建 reg_item（source=用户提供）。"""
    return reg_item_svc.create_manual(user_id=str(user.id), data=data)


@router.get("/items/{item_id}", response_model=RegulatoryRegItemRead)
def get_item(item_id: str, user: CurrentUser, reg_item_svc: RegulatoryRegItemSvc) -> Any:
    return reg_item_svc.get_owned(item_id, user_id=str(user.id))


@router.put("/items/{item_id}", response_model=RegulatoryRegItemRead)
def update_item(
    item_id: str,
    data: RegulatoryRegItemUpdate,
    user: CurrentUser,
    reg_item_svc: RegulatoryRegItemSvc,
) -> Any:
    """更新动态（标记 status、调整 materiality）。"""
    return reg_item_svc.update(item_id, user_id=str(user.id), data=data)


# --- analyses (read history; written by WS agent) ---------------------------


@router.get("/analyses", response_model=RegulatoryAnalysisList)
def list_analyses(
    user: CurrentUser,
    analysis_svc: RegulatoryAnalysisSvc,
    analysis_type: str | None = Query(None),
    reg_item_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = analysis_svc.list_analyses(
        user_id=str(user.id),
        analysis_type=analysis_type,
        reg_item_id=reg_item_id,
        skip=skip,
        limit=limit,
    )
    return RegulatoryAnalysisList(items=items, total=total)


@router.get("/analyses/{analysis_id}", response_model=RegulatoryAnalysisRead)
def get_analysis(analysis_id: str, user: CurrentUser, analysis_svc: RegulatoryAnalysisSvc) -> Any:
    return analysis_svc.get_owned(analysis_id, user_id=str(user.id))


# --- gap tracker (status report + close + risk-accept) ----------------------


@router.get("/gaps", response_model=RegulatoryGapStatusReport)
def gap_status_report(user: CurrentUser, gap_svc: RegulatoryGapSvc) -> Any:
    """差距状态报告（🔴逾期/🟠30天/🟡开放/👀观察/进行中/最近关闭，聚合算术）。"""
    return gap_svc.status_report(str(user.id))


@router.post("/gaps", response_model=RegulatoryGapRead, status_code=status.HTTP_201_CREATED)
def create_gap(data: RegulatoryGapCreate, user: CurrentUser, gap_svc: RegulatoryGapSvc) -> Any:
    """手动建差距。"""
    return gap_svc.create_manual(user_id=str(user.id), data=data)


@router.get("/gaps/{gap_id}", response_model=RegulatoryGapRead)
def get_gap(gap_id: str, user: CurrentUser, gap_svc: RegulatoryGapSvc) -> Any:
    return gap_svc.get_owned(gap_id, user_id=str(user.id))


@router.put("/gaps/{gap_id}", response_model=RegulatoryGapRead)
def update_gap(
    gap_id: str, data: RegulatoryGapUpdate, user: CurrentUser, gap_svc: RegulatoryGapSvc
) -> Any:
    """更新差距（owner / due / status_verified / gap_type / severity）。"""
    return gap_svc.update(gap_id, user_id=str(user.id), data=data)


@router.post("/gaps/{gap_id}/close", response_model=RegulatoryGapRead)
def close_gap(
    gap_id: str, data: RegulatoryGapClose, user: CurrentUser, gap_svc: RegulatoryGapSvc
) -> Any:
    """关闭差距（记 resolution）。"""
    return gap_svc.close(gap_id, user_id=str(user.id), data=data)


@router.post("/gaps/{gap_id}/accept", response_model=RegulatoryGapRead)
def accept_gap_risk(
    gap_id: str, data: RegulatoryGapAccept, user: CurrentUser, gap_svc: RegulatoryGapSvc
) -> Any:
    """风险接受（status→risk-accepted，保留不删，移出开放报告）。"""
    return gap_svc.accept_risk(gap_id, user_id=str(user.id), data=data)


# --- comment-period tracker -------------------------------------------------


@router.get("/comments", response_model=RegulatoryCommentList)
def list_comments(
    user: CurrentUser,
    comment_svc: RegulatoryCommentSvc,
    decision: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = comment_svc.list_paginated(
        user_id=str(user.id), decision=decision, skip=skip, limit=limit
    )
    return RegulatoryCommentList(
        items=items,
        total=total,
        pending_within_30d=comment_svc.pending_within_30d(str(user.id)),
    )


@router.post("/comments/{comment_id}/decide", response_model=RegulatoryCommentRead)
def decide_comment(
    comment_id: str,
    data: RegulatoryCommentDecide,
    user: CurrentUser,
    comment_svc: RegulatoryCommentSvc,
) -> Any:
    """记录决策（filing/not-filing/filed/waived + rationale）。"""
    return comment_svc.decide(comment_id, user_id=str(user.id), data=data)


# --- notifications ----------------------------------------------------------


@router.get("/notifications", response_model=RegulatoryNotificationList)
def list_notifications(
    user: CurrentUser,
    notification_svc: RegulatoryNotificationSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = notification_svc.list_notifications(user_id=str(user.id), skip=skip, limit=limit)
    return RegulatoryNotificationList(items=items, total=total)


@router.post("/notifications/{notification_id}/read", response_model=RegulatoryNotificationRead)
def mark_notification_read(
    notification_id: str, user: CurrentUser, notification_svc: RegulatoryNotificationSvc
) -> Any:
    return notification_svc.mark_read(notification_id, user_id=str(user.id))
