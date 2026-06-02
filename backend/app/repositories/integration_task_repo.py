"""Repository for integration_tasks. Stateless; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.integration_task import IntegrationTask


def get_by_id(db: Session, task_id: str) -> IntegrationTask | None:
    return db.get(IntegrationTask, task_id)


def list_by_deal(
    db: Session, *, deal_id: str, skip: int = 0, limit: int = 200
) -> tuple[list[IntegrationTask], int]:
    base = select(IntegrationTask).where(IntegrationTask.deal_id == deal_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(IntegrationTask.created_at.asc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, deal_id: str, task: str, **fields: Any) -> IntegrationTask:
    row = IntegrationTask(deal_id=deal_id, task=task, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def update(db: Session, *, row: IntegrationTask, **fields: Any) -> IntegrationTask:
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row
