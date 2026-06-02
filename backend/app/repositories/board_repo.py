"""Repositories for board_meetings + board_documents. Stateless; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.board_meeting import BoardDocument, BoardMeeting


def get_meeting(db: Session, meeting_id: str) -> BoardMeeting | None:
    return db.get(BoardMeeting, meeting_id)


def list_meetings(
    db: Session, *, user_id: str, skip: int = 0, limit: int = 100
) -> tuple[list[BoardMeeting], int]:
    base = select(BoardMeeting).where(BoardMeeting.user_id == user_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(BoardMeeting.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create_meeting(db: Session, *, user_id: str, title: str, **fields: Any) -> BoardMeeting:
    row = BoardMeeting(user_id=user_id, title=title, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def get_document(db: Session, doc_id: str) -> BoardDocument | None:
    return db.get(BoardDocument, doc_id)


def list_documents(
    db: Session, *, user_id: str, skip: int = 0, limit: int = 100
) -> tuple[list[BoardDocument], int]:
    base = select(BoardDocument).where(BoardDocument.user_id == user_id)
    total = len(db.execute(base).scalars().all())
    rows = (
        db.execute(base.order_by(BoardDocument.created_at.desc()).offset(skip).limit(limit))
        .scalars()
        .all()
    )
    return list(rows), total


def create_document(db: Session, *, user_id: str, title: str, **fields: Any) -> BoardDocument:
    row = BoardDocument(user_id=user_id, title=title, **fields)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def update_document(db: Session, *, row: BoardDocument, **fields: Any) -> BoardDocument:
    for key, value in fields.items():
        if value is not None:
            setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row
