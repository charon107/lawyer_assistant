"""Commercial-legal module REST endpoints.

WebSocket (`/api/v1/commercial/chat`) lives in a separate file.

The endpoints split cleanly into four groups:

  /status            — Has the user finished cold-start? Drives the
                       "go through setup vs. show main UI" decision
                       in the frontend.
  /setup, /setup/status — The cold-start interview state machine.
  /profile           — Direct read/write of the practice profile
                       (used by the settings page after cold-start).
  /reviews           — Read-only list / detail. Review creation goes
                       through the WebSocket.
"""

from typing import Any

from fastapi import APIRouter, Query, status

from app.api.deps import (
    ColdStartSvc,
    CommercialMatterSvc,
    CommercialNotificationSvc,
    CommercialProfileSvc,
    ContractDeviationSvc,
    ContractReviewSvc,
    CurrentUser,
    PlaybookProposalSvc,
    RenewalSvc,
)
from app.schemas.commercial.cold_start import (
    ColdStartRequest,
    ColdStartResponse,
)
from app.schemas.commercial.deviation import ClauseDeviationCountList
from app.schemas.commercial.matter import (
    CommercialMatterCreate,
    CommercialMatterList,
    CommercialMatterRead,
    CommercialMatterUpdate,
)
from app.schemas.commercial.notification import (
    CommercialNotificationList,
    CommercialNotificationRead,
)
from app.schemas.commercial.profile import (
    CommercialProfileRead,
    CommercialProfileUpdate,
)
from app.schemas.commercial.proposal import (
    PlaybookProposalList,
    PlaybookProposalRead,
    PlaybookProposalUpdate,
)
from app.schemas.commercial.renewal import (
    RenewalRegistrationCreate,
    RenewalRegistrationList,
    RenewalRegistrationRead,
    RenewalRegistrationUpdate,
)
from app.schemas.commercial.review import (
    ContractReviewList,
    ContractReviewRead,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Module-level status
# ---------------------------------------------------------------------------


@router.get("/status")
def get_module_status(
    user: CurrentUser,
    profile_svc: CommercialProfileSvc,
) -> dict[str, Any]:
    """Whether the user has finished commercial-legal cold-start.

    Returns:
        {
            "configured": bool,
            "setup_status": "not_started" | "in_progress" | "completed",
            "side": "sales" | "purchasing" | "both" | null
        }
    """
    profile = profile_svc.get_my_profile_or_none(str(user.id))
    if profile is None:
        return {
            "configured": False,
            "setup_status": "not_started",
            "side": None,
        }
    return {
        "configured": profile.setup_status == "completed",
        "setup_status": profile.setup_status,
        "side": profile.side,
    }


# ---------------------------------------------------------------------------
# Cold-start wizard
# ---------------------------------------------------------------------------


@router.get("/setup/status", response_model=ColdStartResponse)
def get_setup_status(
    user: CurrentUser,
    cold_start_svc: ColdStartSvc,
) -> Any:
    """Where is the user in the 5-step cold-start wizard?"""
    return cold_start_svc.get_progress(str(user.id))


@router.post("/setup", response_model=ColdStartResponse)
def submit_setup_step(
    request: ColdStartRequest,
    user: CurrentUser,
    cold_start_svc: ColdStartSvc,
) -> Any:
    """Persist answers for one wizard step and advance.

    On the final step (4), this also materializes the
    `commercial_profiles` row and flips the module to completed.
    """
    return cold_start_svc.submit_step(str(user.id), request)


# ---------------------------------------------------------------------------
# Practice profile direct access
# ---------------------------------------------------------------------------


@router.get("/profile", response_model=CommercialProfileRead)
def get_my_profile(
    user: CurrentUser,
    profile_svc: CommercialProfileSvc,
) -> Any:
    """The full practice profile for the current user.

    404 if the user has not yet completed cold-start.
    """
    return profile_svc.get_my_profile(str(user.id))


@router.put("/profile", response_model=CommercialProfileRead)
def update_my_profile(
    data: CommercialProfileUpdate,
    user: CurrentUser,
    profile_svc: CommercialProfileSvc,
) -> Any:
    """Replace fields on the practice profile.

    Partial — only fields present in the request body are written.
    """
    return profile_svc.upsert_my_profile(str(user.id), data)


# ---------------------------------------------------------------------------
# Contract reviews (read)
# ---------------------------------------------------------------------------


@router.get("/reviews", response_model=ContractReviewList)
def list_my_reviews(
    user: CurrentUser,
    review_svc: ContractReviewSvc,
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
) -> Any:
    """Paginated history of the current user's contract reviews."""
    items, total = review_svc.list_my_reviews(
        str(user.id),
        skip=skip,
        limit=limit,
    )
    return ContractReviewList(items=items, total=total)  # type: ignore[arg-type]


@router.get("/reviews/{review_id}", response_model=ContractReviewRead)
def get_my_review(
    review_id: str,
    user: CurrentUser,
    review_svc: ContractReviewSvc,
) -> Any:
    """One review detail. 404 if not found, 403 if it belongs to another user."""
    return review_svc.get_my_review(str(user.id), review_id)


# Phase A intentionally does NOT expose POST /reviews — review creation
# happens through the WebSocket (commercial_ws.py) so the streamed
# tool-call events can reach the frontend in real time.


# ---------------------------------------------------------------------------
# Matters (Phase B)
# ---------------------------------------------------------------------------


@router.get("/matters", response_model=CommercialMatterList)
def list_my_matters(
    user: CurrentUser,
    matter_svc: CommercialMatterSvc,
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
) -> Any:
    """Paginated list of the current user's matters."""
    items, total = matter_svc.list_my_matters(str(user.id), skip=skip, limit=limit)
    return CommercialMatterList(items=items, total=total)  # type: ignore[arg-type]


@router.post(
    "/matters",
    response_model=CommercialMatterRead,
    status_code=status.HTTP_201_CREATED,
)
def create_matter(
    data: CommercialMatterCreate,
    user: CurrentUser,
    matter_svc: CommercialMatterSvc,
) -> Any:
    """Create a new matter owned by the current user."""
    return matter_svc.create_matter(str(user.id), data)


@router.get("/matters/{matter_id}", response_model=CommercialMatterRead)
def get_my_matter(
    matter_id: str,
    user: CurrentUser,
    matter_svc: CommercialMatterSvc,
) -> Any:
    """One matter detail. 404 if not found, 403 if it belongs to another user."""
    return matter_svc.get_my_matter(str(user.id), matter_id)


@router.patch("/matters/{matter_id}", response_model=CommercialMatterRead)
def update_my_matter(
    matter_id: str,
    data: CommercialMatterUpdate,
    user: CurrentUser,
    matter_svc: CommercialMatterSvc,
) -> Any:
    """Partial update of an owned matter."""
    return matter_svc.update_my_matter(str(user.id), matter_id, data)


# ---------------------------------------------------------------------------
# Renewals (Phase B)
# ---------------------------------------------------------------------------


@router.get("/renewals", response_model=RenewalRegistrationList)
def list_my_renewals(
    user: CurrentUser,
    renewal_svc: RenewalSvc,
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
) -> Any:
    """Paginated list of the current user's renewal registrations."""
    items, total = renewal_svc.list_my_renewals(str(user.id), skip=skip, limit=limit)
    return RenewalRegistrationList(items=items, total=total)  # type: ignore[arg-type]


@router.post(
    "/renewals",
    response_model=RenewalRegistrationRead,
    status_code=status.HTTP_201_CREATED,
)
def register_renewal(
    data: RenewalRegistrationCreate,
    user: CurrentUser,
    renewal_svc: RenewalSvc,
) -> Any:
    """Register a renewal. The three deadline dates are computed server-side."""
    return renewal_svc.register_renewal(str(user.id), data)


@router.patch("/renewals/{renewal_id}", response_model=RenewalRegistrationRead)
def update_my_renewal(
    renewal_id: str,
    data: RenewalRegistrationUpdate,
    user: CurrentUser,
    renewal_svc: RenewalSvc,
) -> Any:
    """Partial update. Deadlines recompute if any term input changes."""
    return renewal_svc.update_my_renewal(str(user.id), renewal_id, data)


# ---------------------------------------------------------------------------
# Deviations (Phase B, read-only aggregation)
# ---------------------------------------------------------------------------


@router.get("/deviations", response_model=ClauseDeviationCountList)
def list_clause_deviation_counts(
    user: CurrentUser,
    deviation_svc: ContractDeviationSvc,
) -> Any:
    """Per-clause deviation counts for the current user, most frequent first."""
    counts = deviation_svc.list_clause_counts(str(user.id))
    return ClauseDeviationCountList(items=counts, total=len(counts))


# ---------------------------------------------------------------------------
# Playbook proposals (Phase B)
# ---------------------------------------------------------------------------


@router.get("/proposals", response_model=PlaybookProposalList)
def list_my_proposals(
    user: CurrentUser,
    proposal_svc: PlaybookProposalSvc,
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
) -> Any:
    """Paginated list of the current user's playbook update proposals."""
    items, total = proposal_svc.list_my_proposals(str(user.id), skip=skip, limit=limit)
    return PlaybookProposalList(items=items, total=total)  # type: ignore[arg-type]


@router.patch("/proposals/{proposal_id}", response_model=PlaybookProposalRead)
def update_my_proposal(
    proposal_id: str,
    data: PlaybookProposalUpdate,
    user: CurrentUser,
    proposal_svc: PlaybookProposalSvc,
) -> Any:
    """Accept / dismiss / edit an owned proposal."""
    return proposal_svc.update_my_proposal(str(user.id), proposal_id, data)


# ---------------------------------------------------------------------------
# Notifications (Phase C)
# ---------------------------------------------------------------------------


@router.get("/notifications", response_model=CommercialNotificationList)
def list_my_notifications(
    user: CurrentUser,
    notification_svc: CommercialNotificationSvc,
    unread_only: bool = Query(False, description="Return only unread notifications"),
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
) -> Any:
    """The current user's notification inbox, newest first, plus the unread count."""
    items, total, unread = notification_svc.list_my_notifications(
        str(user.id),
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )
    return CommercialNotificationList(items=items, total=total, unread=unread)  # type: ignore[arg-type]


@router.post("/notifications/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_read(
    user: CurrentUser,
    notification_svc: CommercialNotificationSvc,
) -> dict[str, int]:
    """Mark every unread notification for the current user as read."""
    updated = notification_svc.mark_all_read(str(user.id))
    return {"updated": updated}


@router.post("/notifications/{notification_id}/read", response_model=CommercialNotificationRead)
def mark_notification_read(
    notification_id: str,
    user: CurrentUser,
    notification_svc: CommercialNotificationSvc,
) -> Any:
    """Mark one owned notification as read. 404 if missing, 403 if another user's."""
    return notification_svc.mark_read(str(user.id), notification_id)
