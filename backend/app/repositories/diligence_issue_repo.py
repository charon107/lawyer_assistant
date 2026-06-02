"""Repository for `diligence_issues`. Stateless sync functions; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.diligence_issue import DiligenceIssue


def get_by_id(db: Session, issue_id: str) -> DiligenceIssue | None:
    return db.get(DiligenceIssue, issue_id)


def list_by_deal(
    db: Session,
    *,
    deal_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[DiligenceIssue], int]:
    base = select(DiligenceIssue).where(DiligenceIssue.deal_id == deal_id)
    if status is not None:
        base = base.where(DiligenceIssue.status == status)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(DiligenceIssue.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, deal_id: str, title: str, **fields: Any) -> DiligenceIssue:
    issue = DiligenceIssue(deal_id=deal_id, title=title, **fields)
    db.add(issue)
    db.flush()
    db.refresh(issue)
    return issue


def update(db: Session, *, issue: DiligenceIssue, **fields: Any) -> DiligenceIssue:
    for key, value in fields.items():
        if value is not None:
            setattr(issue, key, value)
    db.flush()
    db.refresh(issue)
    return issue


def delete(db: Session, issue_id: str) -> DiligenceIssue | None:
    issue = get_by_id(db, issue_id)
    if issue is not None:
        db.delete(issue)
        db.flush()
    return issue
