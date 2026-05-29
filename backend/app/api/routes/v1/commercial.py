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

from fastapi import APIRouter, Query

from app.api.deps import (
    ColdStartSvc,
    CommercialProfileSvc,
    ContractReviewSvc,
    CurrentUser,
)
from app.schemas.commercial.cold_start import (
    ColdStartRequest,
    ColdStartResponse,
)
from app.schemas.commercial.profile import (
    CommercialProfileRead,
    CommercialProfileUpdate,
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
