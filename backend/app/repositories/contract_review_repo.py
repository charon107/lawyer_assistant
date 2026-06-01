"""Repository for `contract_reviews`.

`result_json` is stored as JSON text; callers may pass a
`ContractReviewResult` (or any pydantic model with `model_dump`) and the
repo serializes it on the way in. Reads return the raw ORM row; the
schema layer handles decoding.
"""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.db.models.contract_review import ContractReview

# Statuses that mean a review run has finished (anything but in_progress/None).
_COMPLETED_STATUSES = ("green", "yellow", "red")


def _to_json(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(), ensure_ascii=False)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        return value
    raise TypeError(f"Cannot serialize {type(value).__name__} as JSON text")


def create(
    db: Session,
    *,
    user_id: str,
    review_type: str,
    counterparty: str | None = None,
    agreement_name: str | None = None,
    agreement_type: str | None = None,
    side: str = "purchasing",
    annual_value: float | None = None,
    file_path: str | None = None,
    file_name: str | None = None,
    matter_id: str | None = None,
    result_status: str = "in_progress",
) -> ContractReview:
    """Create a review row in the in_progress state.

    The agent fills in result fields via `update_result` once streaming
    completes.
    """
    review = ContractReview(
        user_id=user_id,
        review_type=review_type,
        counterparty=counterparty,
        agreement_name=agreement_name,
        agreement_type=agreement_type,
        side=side,
        annual_value=annual_value,
        file_path=file_path,
        file_name=file_name,
        matter_id=matter_id,
        result_status=result_status,
    )
    db.add(review)
    db.flush()
    db.refresh(review)
    return review


def get_by_id(db: Session, review_id: str) -> ContractReview | None:
    return db.get(ContractReview, review_id)


def list_by_user(
    db: Session,
    user_id: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[ContractReview], int]:
    """Return `(items, total)` for paginated history view."""
    total = db.execute(
        select(func.count(ContractReview.id)).where(ContractReview.user_id == user_id)
    ).scalar_one()
    # Secondary order by id so the result is deterministic even when
    # rows share the same created_at (common in tests and rapid bursts).
    items = (
        db.execute(
            select(ContractReview)
            .where(ContractReview.user_id == user_id)
            .order_by(desc(ContractReview.created_at), desc(ContractReview.id))
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(items), total


def list_completed_between(
    db: Session,
    *,
    user_id: str,
    since: datetime,
    until: datetime,
) -> list[ContractReview]:
    """Return completed reviews created in the half-open window `[since, until)`.

    The weekly deal-debrief reads each review's stored `result_json` to build a
    recap, so only finished runs (`result_status` in green/yellow/red) are
    returned. Ordered oldest-first so the recap reads chronologically.
    """
    items = (
        db.execute(
            select(ContractReview)
            .where(
                ContractReview.user_id == user_id,
                ContractReview.result_status.in_(_COMPLETED_STATUSES),
                ContractReview.created_at >= since,
                ContractReview.created_at < until,
            )
            .order_by(asc(ContractReview.created_at), asc(ContractReview.id))
        )
        .scalars()
        .all()
    )
    return list(items)


def update_result(
    db: Session,
    *,
    review: ContractReview,
    result_status: str | None = None,
    result_summary: str | None = None,
    result_memo: str | None = None,
    result_json: Any = None,
    stakeholder_summary: str | None = None,
    required_approver: str | None = None,
    escalation_sent: bool | None = None,
) -> ContractReview:
    """Patch the result fields of an in-progress review."""
    if result_status is not None:
        review.result_status = result_status
    if result_summary is not None:
        review.result_summary = result_summary
    if result_memo is not None:
        review.result_memo = result_memo
    if result_json is not None:
        review.result_json = _to_json(result_json)
    if stakeholder_summary is not None:
        review.stakeholder_summary = stakeholder_summary
    if required_approver is not None:
        review.required_approver = required_approver
    if escalation_sent is not None:
        review.escalation_sent = escalation_sent

    db.flush()
    db.refresh(review)
    return review


def delete(db: Session, review: ContractReview) -> ContractReview:
    db.delete(review)
    db.flush()
    return review
