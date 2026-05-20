"""System log repository — pure data access."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.system_log import SystemLog


def create(
    db: Session,
    *,
    level: str,
    category: str,
    action: str,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata_json: str | None = None,
    ip_address: str | None = None,
    request_id: str | None = None,
) -> SystemLog:
    log = SystemLog(
        level=level,
        category=category,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=metadata_json,
        ip_address=ip_address,
        request_id=request_id,
    )
    db.add(log)
    db.flush()
    db.refresh(log)
    return log


def list_logs(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    category: str | None = None,
    action: str | None = None,
    user_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> tuple[list[SystemLog], int]:
    q = select(SystemLog)
    if category:
        q = q.where(SystemLog.category == category)
    if action:
        q = q.where(SystemLog.action == action)
    if user_id:
        q = q.where(SystemLog.user_id == user_id)
    if since:
        q = q.where(SystemLog.created_at >= since)
    if until:
        q = q.where(SystemLog.created_at <= until)

    count_q = select(func.count()).select_from(q.subquery())
    total = db.execute(count_q).scalar_one()

    items = (
        db.execute(q.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(items), total


def count_by_category(db: Session, *, since: datetime | None = None) -> dict[str, int]:
    q = select(SystemLog.category, func.count(SystemLog.id).label("cnt")).group_by(
        SystemLog.category
    )
    if since:
        q = q.where(SystemLog.created_at >= since)
    rows = db.execute(q).all()
    return {row.category: row.cnt for row in rows}


def count_by_action(db: Session, *, category: str, since: datetime | None = None) -> dict[str, int]:
    q = (
        select(SystemLog.action, func.count(SystemLog.id).label("cnt"))
        .where(SystemLog.category == category)
        .group_by(SystemLog.action)
    )
    if since:
        q = q.where(SystemLog.created_at >= since)
    rows = db.execute(q).all()
    return {row.action: row.cnt for row in rows}


def total_count(db: Session) -> int:
    return db.execute(select(func.count(SystemLog.id))).scalar_one()


def count_since(db: Session, *, since: datetime) -> int:
    return db.execute(
        select(func.count(SystemLog.id)).where(SystemLog.created_at >= since)
    ).scalar_one()
