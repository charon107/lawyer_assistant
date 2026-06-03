"""Repository for internal-investigation tables. Stateless sync; never commits.

Covers the matter header plus its structured children (log entries, sources
checklist, evidentiary gaps). Sequence numbers (entry_seq / source_seq /
gap_seq) are assigned per investigation as max+1.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.employment_investigation import (
    EmploymentInvestigation,
    InvestigationGap,
    InvestigationLogEntry,
    InvestigationSource,
)

# ----- matter header --------------------------------------------------------


def get_by_id(db: Session, investigation_id: str) -> EmploymentInvestigation | None:
    return db.get(EmploymentInvestigation, investigation_id)


def get_by_name(db: Session, *, user_id: str, name: str) -> EmploymentInvestigation | None:
    result = db.execute(
        select(EmploymentInvestigation).where(
            EmploymentInvestigation.user_id == user_id,
            EmploymentInvestigation.investigation_name == name,
        )
    )
    return result.scalar_one_or_none()


def list_by_user(
    db: Session,
    *,
    user_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[EmploymentInvestigation], int]:
    base = select(EmploymentInvestigation).where(EmploymentInvestigation.user_id == user_id)
    if status is not None:
        base = base.where(EmploymentInvestigation.status == status)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(
            base.order_by(EmploymentInvestigation.created_at.desc()).offset(skip).limit(limit)
        )
        .scalars()
        .all()
    )
    return list(rows), total


def create(
    db: Session, *, user_id: str, investigation_name: str, **fields: Any
) -> EmploymentInvestigation:
    inv = EmploymentInvestigation(user_id=user_id, investigation_name=investigation_name, **fields)
    db.add(inv)
    db.flush()
    db.refresh(inv)
    return inv


def update(
    db: Session, *, investigation: EmploymentInvestigation, **fields: Any
) -> EmploymentInvestigation:
    for key, value in fields.items():
        if value is not None:
            setattr(investigation, key, value)
    db.flush()
    db.refresh(investigation)
    return investigation


# ----- log entries ----------------------------------------------------------


def _next_seq(db: Session, model: Any, investigation_id: str, seq_col: Any) -> int:
    current = db.execute(
        select(func.max(seq_col)).where(model.investigation_id == investigation_id)
    ).scalar_one_or_none()
    return (current or 0) + 1


def append_log_entry(db: Session, *, investigation_id: str, **fields: Any) -> InvestigationLogEntry:
    seq = _next_seq(db, InvestigationLogEntry, investigation_id, InvestigationLogEntry.entry_seq)
    entry = InvestigationLogEntry(investigation_id=investigation_id, entry_seq=seq, **fields)
    db.add(entry)
    db.flush()
    db.refresh(entry)
    return entry


def list_log_entries(db: Session, *, investigation_id: str) -> list[InvestigationLogEntry]:
    rows = (
        db.execute(
            select(InvestigationLogEntry)
            .where(InvestigationLogEntry.investigation_id == investigation_id)
            .order_by(InvestigationLogEntry.entry_seq)
        )
        .scalars()
        .all()
    )
    return list(rows)


# ----- sources checklist ----------------------------------------------------


def add_source(
    db: Session, *, investigation_id: str, source: str, **fields: Any
) -> InvestigationSource:
    seq = _next_seq(db, InvestigationSource, investigation_id, InvestigationSource.source_seq)
    row = InvestigationSource(
        investigation_id=investigation_id, source_seq=seq, source=source, **fields
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def list_sources(db: Session, *, investigation_id: str) -> list[InvestigationSource]:
    rows = (
        db.execute(
            select(InvestigationSource)
            .where(InvestigationSource.investigation_id == investigation_id)
            .order_by(InvestigationSource.source_seq)
        )
        .scalars()
        .all()
    )
    return list(rows)


def get_source(db: Session, source_id: str) -> InvestigationSource | None:
    return db.get(InvestigationSource, source_id)


def update_source(
    db: Session, *, source: InvestigationSource, **fields: Any
) -> InvestigationSource:
    for key, value in fields.items():
        if value is not None:
            setattr(source, key, value)
    db.flush()
    db.refresh(source)
    return source


# ----- evidentiary gaps -----------------------------------------------------


def add_gap(
    db: Session, *, investigation_id: str, description: str, **fields: Any
) -> InvestigationGap:
    seq = _next_seq(db, InvestigationGap, investigation_id, InvestigationGap.gap_seq)
    row = InvestigationGap(
        investigation_id=investigation_id, gap_seq=seq, description=description, **fields
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def list_gaps(db: Session, *, investigation_id: str) -> list[InvestigationGap]:
    rows = (
        db.execute(
            select(InvestigationGap)
            .where(InvestigationGap.investigation_id == investigation_id)
            .order_by(InvestigationGap.gap_seq)
        )
        .scalars()
        .all()
    )
    return list(rows)
