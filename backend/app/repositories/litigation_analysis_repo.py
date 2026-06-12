"""Repository for `litigation_analyses`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.litigation_analysis import LitigationAnalysis


def get_by_id(db: Session, analysis_id: str) -> LitigationAnalysis | None:
    return db.get(LitigationAnalysis, analysis_id)


def list_by_user(
    db: Session,
    *,
    user_id: str,
    analysis_type: str | None = None,
    matter_id: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[LitigationAnalysis], int]:
    """列表：按用户过滤，可选按 analysis_type / matter_id 过滤。"""
    base = select(LitigationAnalysis).where(LitigationAnalysis.user_id == user_id)
    count_q = (
        select(func.count())
        .select_from(LitigationAnalysis)
        .where(LitigationAnalysis.user_id == user_id)
    )
    if analysis_type is not None:
        base = base.where(LitigationAnalysis.analysis_type == analysis_type)
        count_q = count_q.where(LitigationAnalysis.analysis_type == analysis_type)
    if matter_id is not None:
        base = base.where(LitigationAnalysis.matter_id == matter_id)
        count_q = count_q.where(LitigationAnalysis.matter_id == matter_id)

    total = int(db.execute(count_q).scalar_one())
    rows = (
        db.execute(base.order_by(LitigationAnalysis.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def list_by_subject(
    db: Session, *, user_id: str, subject: str, limit: int = 20
) -> list[LitigationAnalysis]:
    """Prior-context lookup — same subject (案件名/证人/调查令来源)。"""
    rows = (
        db.execute(
            select(LitigationAnalysis)
            .where(
                LitigationAnalysis.user_id == user_id,
                LitigationAnalysis.subject == subject,
            )
            .order_by(LitigationAnalysis.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(rows)


def list_legal_holds_by_user(db: Session, *, user_id: str) -> list[LitigationAnalysis]:
    """拉取用户所有 legal_hold 分析（供 docket-watcher 扫描 next_refresh）。"""
    rows = (
        db.execute(
            select(LitigationAnalysis).where(
                LitigationAnalysis.user_id == user_id,
                LitigationAnalysis.analysis_type == "legal_hold",
            )
        )
        .scalars()
        .all()
    )
    return list(rows)


def create(db: Session, *, user_id: str, analysis_type: str, **fields: Any) -> LitigationAnalysis:
    analysis = LitigationAnalysis(user_id=user_id, analysis_type=analysis_type, **fields)
    db.add(analysis)
    db.flush()
    db.refresh(analysis)
    return analysis


def update(db: Session, *, analysis: LitigationAnalysis, **fields: Any) -> LitigationAnalysis:
    for key, value in fields.items():
        if value is not None:
            setattr(analysis, key, value)
    db.flush()
    db.refresh(analysis)
    return analysis
