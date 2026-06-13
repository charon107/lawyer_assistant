"""Repository for `regulatory_analyses`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.regulatory_analysis import RegulatoryAnalysis


def get_by_id(db: Session, analysis_id: str) -> RegulatoryAnalysis | None:
    return db.get(RegulatoryAnalysis, analysis_id)


def list_by_subject(db: Session, *, user_id: str, subject: str) -> list[RegulatoryAnalysis]:
    """Prior analyses by subject (支撑跨技能严重性底线)."""
    result = db.execute(
        select(RegulatoryAnalysis)
        .where(RegulatoryAnalysis.user_id == user_id, RegulatoryAnalysis.subject == subject)
        .order_by(RegulatoryAnalysis.created_at.desc())
    )
    return list(result.scalars().all())


def list_paginated(
    db: Session,
    *,
    user_id: str,
    analysis_type: str | None = None,
    reg_item_id: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[RegulatoryAnalysis], int]:
    conditions = [RegulatoryAnalysis.user_id == user_id]
    if analysis_type is not None:
        conditions.append(RegulatoryAnalysis.analysis_type == analysis_type)
    if reg_item_id is not None:
        conditions.append(RegulatoryAnalysis.reg_item_id == reg_item_id)

    total = db.execute(
        select(func.count()).select_from(RegulatoryAnalysis).where(*conditions)
    ).scalar_one()
    result = db.execute(
        select(RegulatoryAnalysis)
        .where(*conditions)
        .order_by(RegulatoryAnalysis.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all()), total


def create(db: Session, *, user_id: str, **fields: Any) -> RegulatoryAnalysis:
    analysis = RegulatoryAnalysis(user_id=user_id, **fields)
    db.add(analysis)
    db.flush()
    db.refresh(analysis)
    return analysis


def update(db: Session, *, analysis: RegulatoryAnalysis, **fields: Any) -> RegulatoryAnalysis:
    for key, value in fields.items():
        if value is not None:
            setattr(analysis, key, value)
    db.flush()
    db.refresh(analysis)
    return analysis
