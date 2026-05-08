"""LPA Case repository (SQLite sync)."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.chat_file import ChatFile
from app.db.models.conversation import Conversation
from app.db.models.lpa_case import LPACase


def create_case(
    db: Session,
    *,
    user_id: str,
    name: str,
    description: str | None = None,
    document_type: str = "lpa",
) -> LPACase:
    """Create a new LPA case."""
    case = LPACase(user_id=user_id, name=name, description=description, document_type=document_type)
    db.add(case)
    db.flush()
    db.refresh(case)
    return case


def get_case_by_id(db: Session, case_id: str) -> LPACase | None:
    """Get an LPA case by ID."""
    return db.get(LPACase, case_id)


def get_case_by_id_with_documents(db: Session, case_id: str) -> LPACase | None:
    """Get an LPA case by ID with documents eagerly loaded."""
    query = (
        select(LPACase)
        .options(selectinload(LPACase.documents))
        .where(LPACase.id == case_id)
    )
    result = db.execute(query)
    return result.scalar_one_or_none()


def get_cases_by_user(
    db: Session,
    user_id: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[tuple[LPACase, int]]:
    """Get LPA cases for a user with document count.

    Returns list of (case, document_count) tuples.
    Uses selectinload to prevent N+1 on documents.
    """
    doc_count_subq = (
        select(func.count(ChatFile.id))
        .where(ChatFile.case_id == LPACase.id)
        .correlate(LPACase)
        .scalar_subquery()
    )

    query = (
        select(LPACase, doc_count_subq.label("document_count"))
        .where(LPACase.user_id == user_id)
        .where(LPACase.status == "active")
        .order_by(LPACase.updated_at.desc().nullslast(), LPACase.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = db.execute(query)
    return list(result.all())


def count_cases_by_user(db: Session, user_id: str) -> int:
    """Count active cases for a user."""
    query = select(func.count(LPACase.id)).where(
        LPACase.user_id == user_id, LPACase.status == "active"
    )
    return db.execute(query).scalar() or 0


def update_case(
    db: Session,
    *,
    db_case: LPACase,
    update_data: dict[str, Any],
) -> LPACase:
    """Update an LPA case."""
    for field, value in update_data.items():
        setattr(db_case, field, value)
    db.flush()
    db.refresh(db_case)
    return db_case


def delete_case(db: Session, case_id: str) -> bool:
    """Delete an LPA case (cascades to documents and conversations)."""
    case = get_case_by_id(db, case_id)
    if case:
        db.delete(case)
        db.flush()
        return True
    return False


def create_document(
    db: Session,
    *,
    user_id: str,
    case_id: str,
    filename: str,
    mime_type: str,
    size: int,
    storage_path: str,
    file_type: str,
    parsed_content: str | None = None,
) -> ChatFile:
    """Create a document linked to a case."""
    chat_file = ChatFile(
        user_id=user_id,
        case_id=case_id,
        filename=filename,
        mime_type=mime_type,
        size=size,
        storage_path=storage_path,
        file_type=file_type,
        parsed_content=parsed_content,
    )
    db.add(chat_file)
    db.flush()
    db.refresh(chat_file)
    return chat_file


def get_documents_by_case(db: Session, case_id: str) -> list[ChatFile]:
    """Get all documents for a case."""
    query = (
        select(ChatFile)
        .where(ChatFile.case_id == case_id)
        .order_by(ChatFile.created_at.desc())
    )
    result = db.execute(query)
    return list(result.scalars().all())


def get_document_by_id(db: Session, doc_id: str) -> ChatFile | None:
    """Get a document by ID."""
    return db.get(ChatFile, doc_id)


def delete_document(db: Session, doc_id: str) -> bool:
    """Delete a document."""
    doc = get_document_by_id(db, doc_id)
    if doc:
        db.delete(doc)
        db.flush()
        return True
    return False


def update_document_summary(db: Session, doc_id: str, summary: str) -> ChatFile | None:
    """Update document summary."""
    doc = get_document_by_id(db, doc_id)
    if doc:
        doc.summary = summary
        db.flush()
        db.refresh(doc)
    return doc


def get_conversations_by_case(
    db: Session,
    case_id: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[Conversation]:
    """Get conversations for a case."""
    query = (
        select(Conversation)
        .where(Conversation.case_id == case_id)
        .where(Conversation.is_archived == False)  # noqa: E712
        .order_by(Conversation.updated_at.desc().nullslast(), Conversation.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = db.execute(query)
    return list(result.scalars().all())
