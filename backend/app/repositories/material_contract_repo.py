"""Repository for `material_contract_items`. Stateless; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.material_contract_item import MaterialContractItem


def get_by_id(db: Session, item_id: str) -> MaterialContractItem | None:
    return db.get(MaterialContractItem, item_id)


def list_by_deal(
    db: Session,
    *,
    deal_id: str,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[MaterialContractItem], int]:
    base = select(MaterialContractItem).where(MaterialContractItem.deal_id == deal_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(MaterialContractItem.created_at.asc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, deal_id: str, contract: str, **fields: Any) -> MaterialContractItem:
    row = MaterialContractItem(deal_id=deal_id, contract=contract, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def update(db: Session, *, row: MaterialContractItem, **fields: Any) -> MaterialContractItem:
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


def delete(db: Session, item_id: str) -> MaterialContractItem | None:
    row = get_by_id(db, item_id)
    if row is not None:
        db.delete(row)
        db.flush()
    return row
