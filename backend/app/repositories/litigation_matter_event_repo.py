"""Repository for `litigation_matter_events`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.litigation_matter_event import LitigationMatterEvent


def get_by_id(db: Session, event_id: str) -> LitigationMatterEvent | None:
    return db.get(LitigationMatterEvent, event_id)


def list_by_matter(
    db: Session, *, matter_id: str, skip: int = 0, limit: int = 200
) -> list[LitigationMatterEvent]:
    """按 matter_id 拉取时间线（按 event_date 倒序）。"""
    rows = (
        db.execute(
            select(LitigationMatterEvent)
            .where(LitigationMatterEvent.matter_id == matter_id)
            .order_by(LitigationMatterEvent.event_date.desc())
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(rows)


def list_deadlines_by_user(db: Session, *, user_id: str) -> list[LitigationMatterEvent]:
    """拉取用户所有 deadline 类型事件（供 docket-watcher 扫描）。"""
    rows = (
        db.execute(
            select(LitigationMatterEvent)
            .where(
                LitigationMatterEvent.user_id == user_id,
                LitigationMatterEvent.event_type == "deadline",
            )
            .order_by(LitigationMatterEvent.due_date.asc())
        )
        .scalars()
        .all()
    )
    return list(rows)


def create(db: Session, *, matter_id: str, user_id: str, **fields: Any) -> LitigationMatterEvent:
    event = LitigationMatterEvent(matter_id=matter_id, user_id=user_id, **fields)
    db.add(event)
    db.flush()
    db.refresh(event)
    return event
