"""Repository for `playbook_proposals`.

A proposal suggests updating a playbook clause position after that clause has
been deviated from often enough. Standard CRUD plus `list_pending`, which the
proposals review view uses to surface proposals awaiting a lawyer's decision.
"""

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.db.models.playbook_proposal import PlaybookProposal


def create(
    db: Session,
    *,
    user_id: str,
    clause_key: str,
    clause_label: str | None = None,
    current_position: str | None = None,
    proposed_position: str | None = None,
    deviation_count: int = 0,
    status: str = "pending",
    rationale: str | None = None,
) -> PlaybookProposal:
    proposal = PlaybookProposal(
        user_id=user_id,
        clause_key=clause_key,
        clause_label=clause_label,
        current_position=current_position,
        proposed_position=proposed_position,
        deviation_count=deviation_count,
        status=status,
        rationale=rationale,
    )
    db.add(proposal)
    db.flush()
    db.refresh(proposal)
    return proposal


def get_by_id(db: Session, proposal_id: str) -> PlaybookProposal | None:
    return db.get(PlaybookProposal, proposal_id)


def get_pending_by_clause(db: Session, *, user_id: str, clause_key: str) -> PlaybookProposal | None:
    """Return the open proposal for a clause, if one already exists.

    The playbook-monitor calls this to avoid raising a duplicate proposal for
    a clause that already has one pending.
    """
    return db.execute(
        select(PlaybookProposal).where(
            PlaybookProposal.user_id == user_id,
            PlaybookProposal.clause_key == clause_key,
            PlaybookProposal.status == "pending",
        )
    ).scalar_one_or_none()


def list_by_user(
    db: Session,
    user_id: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[PlaybookProposal], int]:
    """Return `(items, total)` for the proposals list view."""
    total = db.execute(
        select(func.count(PlaybookProposal.id)).where(PlaybookProposal.user_id == user_id)
    ).scalar_one()
    items = (
        db.execute(
            select(PlaybookProposal)
            .where(PlaybookProposal.user_id == user_id)
            .order_by(desc(PlaybookProposal.created_at), desc(PlaybookProposal.id))
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(items), total


def list_pending(db: Session, *, user_id: str) -> list[PlaybookProposal]:
    """Return all pending proposals for a user, most-deviated first."""
    items = (
        db.execute(
            select(PlaybookProposal)
            .where(
                PlaybookProposal.user_id == user_id,
                PlaybookProposal.status == "pending",
            )
            .order_by(desc(PlaybookProposal.deviation_count), asc(PlaybookProposal.id))
        )
        .scalars()
        .all()
    )
    return list(items)


def update(
    db: Session,
    *,
    proposal: PlaybookProposal,
    clause_label: str | None = None,
    current_position: str | None = None,
    proposed_position: str | None = None,
    deviation_count: int | None = None,
    status: str | None = None,
    rationale: str | None = None,
) -> PlaybookProposal:
    """Partial update — typically used to accept or dismiss a proposal."""
    if clause_label is not None:
        proposal.clause_label = clause_label
    if current_position is not None:
        proposal.current_position = current_position
    if proposed_position is not None:
        proposal.proposed_position = proposed_position
    if deviation_count is not None:
        proposal.deviation_count = deviation_count
    if status is not None:
        proposal.status = status
    if rationale is not None:
        proposal.rationale = rationale

    db.flush()
    db.refresh(proposal)
    return proposal


def delete(db: Session, proposal: PlaybookProposal) -> PlaybookProposal:
    db.delete(proposal)
    db.flush()
    return proposal
