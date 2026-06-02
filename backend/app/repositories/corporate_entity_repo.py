"""Repositories for corporate_entities + entity_compliance_items. Stateless."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.corporate_entity import CorporateEntity, EntityComplianceItem


def get_entity(db: Session, entity_id: str) -> CorporateEntity | None:
    return db.get(CorporateEntity, entity_id)


def list_entities(
    db: Session, *, user_id: str, skip: int = 0, limit: int = 100
) -> tuple[list[CorporateEntity], int]:
    base = select(CorporateEntity).where(CorporateEntity.user_id == user_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(CorporateEntity.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create_entity(db: Session, *, user_id: str, name: str, **fields: Any) -> CorporateEntity:
    row = CorporateEntity(user_id=user_id, name=name, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def update_entity(db: Session, *, row: CorporateEntity, **fields: Any) -> CorporateEntity:
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


def get_compliance(db: Session, item_id: str) -> EntityComplianceItem | None:
    return db.get(EntityComplianceItem, item_id)


def list_compliance(
    db: Session, *, entity_id: str, skip: int = 0, limit: int = 200
) -> tuple[list[EntityComplianceItem], int]:
    base = select(EntityComplianceItem).where(EntityComplianceItem.entity_id == entity_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(EntityComplianceItem.created_at.asc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create_compliance(
    db: Session, *, entity_id: str, filing_type: str, **fields: Any
) -> EntityComplianceItem:
    row = EntityComplianceItem(entity_id=entity_id, filing_type=filing_type, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def update_compliance(
    db: Session, *, row: EntityComplianceItem, **fields: Any
) -> EntityComplianceItem:
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row
