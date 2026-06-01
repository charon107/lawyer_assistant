"""Repository for `contract_deviations`.

One row per clause where a reviewed contract diverged from the playbook.
Beyond standard CRUD this exposes two aggregations the playbook-monitor and
the deviations dashboard rely on:

- `count_by_clause` — how many times a single clause family has been deviated
  from since a cutoff (drives the "≥5 in 12 months → propose update" rule).
- `aggregate_by_clause` — per-clause counts across the whole portfolio.
"""

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models.contract_deviation import ContractDeviation


def create(
    db: Session,
    *,
    user_id: str,
    review_id: str,
    clause_key: str,
    clause_label: str | None = None,
    playbook_position: str | None = None,
    signed_position: str | None = None,
    severity_legal: str = "green",
    severity_commercial: str = "green",
    category: str | None = None,
) -> ContractDeviation:
    deviation = ContractDeviation(
        user_id=user_id,
        review_id=review_id,
        clause_key=clause_key,
        clause_label=clause_label,
        playbook_position=playbook_position,
        signed_position=signed_position,
        severity_legal=severity_legal,
        severity_commercial=severity_commercial,
        category=category,
    )
    db.add(deviation)
    db.flush()
    db.refresh(deviation)
    return deviation


def get_by_id(db: Session, deviation_id: str) -> ContractDeviation | None:
    return db.get(ContractDeviation, deviation_id)


def list_by_user(
    db: Session,
    user_id: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[ContractDeviation], int]:
    """Return `(items, total)` for the raw deviations list view."""
    total = db.execute(
        select(func.count(ContractDeviation.id)).where(ContractDeviation.user_id == user_id)
    ).scalar_one()
    items = (
        db.execute(
            select(ContractDeviation)
            .where(ContractDeviation.user_id == user_id)
            .order_by(desc(ContractDeviation.created_at), desc(ContractDeviation.id))
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(items), total


def list_by_review(db: Session, review_id: str) -> list[ContractDeviation]:
    """Return all deviations persisted for one review, oldest first."""
    items = (
        db.execute(
            select(ContractDeviation)
            .where(ContractDeviation.review_id == review_id)
            .order_by(ContractDeviation.created_at, ContractDeviation.id)
        )
        .scalars()
        .all()
    )
    return list(items)


def count_by_clause(
    db: Session,
    *,
    user_id: str,
    clause_key: str,
    since: datetime | None = None,
) -> int:
    """Count deviations for one clause family, optionally within a window.

    `since` bounds the rolling window (e.g. 12 months ago) used by the
    playbook-monitor's deviation threshold.
    """
    stmt = select(func.count(ContractDeviation.id)).where(
        ContractDeviation.user_id == user_id,
        ContractDeviation.clause_key == clause_key,
    )
    if since is not None:
        stmt = stmt.where(ContractDeviation.created_at >= since)
    return db.execute(stmt).scalar_one()


def aggregate_by_clause(
    db: Session,
    *,
    user_id: str,
    since: datetime | None = None,
) -> list[tuple[str, str | None, int]]:
    """Return per-clause `(clause_key, clause_label, count)` tuples, most
    frequent first. `clause_label` is the most recent label seen for the key.
    """
    stmt = (
        select(
            ContractDeviation.clause_key,
            func.max(ContractDeviation.clause_label),
            func.count(ContractDeviation.id),
        )
        .where(ContractDeviation.user_id == user_id)
        .group_by(ContractDeviation.clause_key)
        .order_by(desc(func.count(ContractDeviation.id)), ContractDeviation.clause_key)
    )
    if since is not None:
        stmt = stmt.where(ContractDeviation.created_at >= since)
    rows = db.execute(stmt).all()
    return [(key, label, count) for key, label, count in rows]


def delete(db: Session, deviation: ContractDeviation) -> ContractDeviation:
    db.delete(deviation)
    db.flush()
    return deviation
