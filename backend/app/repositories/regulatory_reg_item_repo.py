"""Repository for `regulatory_reg_items`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.regulatory_reg_item import RegulatoryRegItem


def get_by_id(db: Session, item_id: str) -> RegulatoryRegItem | None:
    return db.get(RegulatoryRegItem, item_id)


def list_by_user(db: Session, *, user_id: str) -> list[RegulatoryRegItem]:
    """Full list for a user (cron consumption)."""
    result = db.execute(
        select(RegulatoryRegItem)
        .where(RegulatoryRegItem.user_id == user_id)
        .order_by(RegulatoryRegItem.created_at.desc())
    )
    return list(result.scalars().all())


def find_by_dedup_key(db: Session, *, user_id: str, dedup_key: str) -> RegulatoryRegItem | None:
    """cron 去重：同一用户下相同 dedup_key 视为已抓取。"""
    result = db.execute(
        select(RegulatoryRegItem).where(
            RegulatoryRegItem.user_id == user_id,
            RegulatoryRegItem.dedup_key == dedup_key,
        )
    )
    return result.scalars().first()


def list_paginated(
    db: Session,
    *,
    user_id: str,
    materiality: str | None = None,
    item_type: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[RegulatoryRegItem], int]:
    """REST list with optional materiality/item_type/status filters."""
    conditions = [RegulatoryRegItem.user_id == user_id]
    if materiality is not None:
        conditions.append(RegulatoryRegItem.materiality == materiality)
    if item_type is not None:
        conditions.append(RegulatoryRegItem.item_type == item_type)
    if status is not None:
        conditions.append(RegulatoryRegItem.status == status)

    total = db.execute(
        select(func.count()).select_from(RegulatoryRegItem).where(*conditions)
    ).scalar_one()
    result = db.execute(
        select(RegulatoryRegItem)
        .where(*conditions)
        .order_by(RegulatoryRegItem.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all()), total


def create(db: Session, *, user_id: str, **fields: Any) -> RegulatoryRegItem:
    item = RegulatoryRegItem(user_id=user_id, **fields)
    db.add(item)
    db.flush()
    db.refresh(item)
    return item


def update(db: Session, *, item: RegulatoryRegItem, **fields: Any) -> RegulatoryRegItem:
    for key, value in fields.items():
        if value is not None:
            setattr(item, key, value)
    db.flush()
    db.refresh(item)
    return item
