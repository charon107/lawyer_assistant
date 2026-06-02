"""Repository for `vdr_documents`. Stateless sync functions; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.vdr_document import VdrDocument


def get_by_id(db: Session, doc_id: str) -> VdrDocument | None:
    return db.get(VdrDocument, doc_id)


def list_by_deal(
    db: Session,
    *,
    deal_id: str,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[VdrDocument], int]:
    base = select(VdrDocument).where(VdrDocument.deal_id == deal_id)
    if status is not None:
        base = base.where(VdrDocument.status == status)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(VdrDocument.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create(db: Session, *, deal_id: str, filename: str, **fields: Any) -> VdrDocument:
    doc = VdrDocument(deal_id=deal_id, filename=filename, **fields)
    db.add(doc)
    db.flush()
    db.refresh(doc)
    return doc


def update(db: Session, *, doc: VdrDocument, **fields: Any) -> VdrDocument:
    for key, value in fields.items():
        if value is not None:
            setattr(doc, key, value)
    db.flush()
    db.refresh(doc)
    return doc


def delete(db: Session, doc_id: str) -> VdrDocument | None:
    doc = get_by_id(db, doc_id)
    if doc is not None:
        db.delete(doc)
        db.flush()
    return doc
