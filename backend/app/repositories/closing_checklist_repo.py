"""Repository for `closing_checklist_items`. Stateless; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.closing_checklist_item import ClosingChecklistItem


def get_by_id(db: Session, item_id: str) -> ClosingChecklistItem | None:
    return db.get(ClosingChecklistItem, item_id)


def list_by_deal(
    db: Session,
    *,
    deal_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[ClosingChecklistItem], int]:
    base = select(ClosingChecklistItem).where(ClosingChecklistItem.deal_id == deal_id)
    if status is not None:
        base = base.where(ClosingChecklistItem.status == status)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(ClosingChecklistItem.created_at.asc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, deal_id: str, item: str, **fields: Any) -> ClosingChecklistItem:
    row = ClosingChecklistItem(deal_id=deal_id, item=item, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def update(db: Session, *, row: ClosingChecklistItem, **fields: Any) -> ClosingChecklistItem:
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


def delete(db: Session, item_id: str) -> ClosingChecklistItem | None:
    row = get_by_id(db, item_id)
    if row is not None:
        db.delete(row)
        db.flush()
    return row
