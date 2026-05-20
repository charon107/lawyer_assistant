"""Case repository (SQLite sync)."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.chat_file import ChatFile
from app.db.models.conversation import Conversation
from app.db.models.document_analysis import DocumentAnalysis
from app.db.models.lpa_case import Case


def create_case(
    db: Session,
    *,
    user_id: str,
    name: str,
    description: str | None = None,
    document_type: str = "lpa",
) -> Case:
    """Create a new LPA case."""
    case = Case(user_id=user_id, name=name, description=description, document_type=document_type)
    db.add(case)
    db.flush()
    db.refresh(case)
    return case


def get_case_by_id(db: Session, case_id: str) -> Case | None:
    """Get an LPA case by ID."""
    return db.get(Case, case_id)


def get_case_by_id_with_documents(db: Session, case_id: str) -> Case | None:
    """Get an LPA case by ID with documents eagerly loaded."""
    query = select(Case).options(selectinload(Case.documents)).where(Case.id == case_id)
    result = db.execute(query)
    return result.scalar_one_or_none()


def get_cases_by_user(
    db: Session,
    user_id: str,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[tuple[Case, int]]:
    """Get LPA cases for a user with document count.

    Returns list of (case, document_count) tuples.
    Uses selectinload to prevent N+1 on documents.
    """
    doc_count_subq = (
        select(func.count(ChatFile.id))
        .where(ChatFile.case_id == Case.id)
        .correlate(Case)
        .scalar_subquery()
    )

    query = (
        select(Case, doc_count_subq.label("document_count"))
        .where(Case.user_id == user_id)
        .where(Case.status == "active")
        .order_by(Case.updated_at.desc().nullslast(), Case.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = db.execute(query)
    return list(result.all())


def count_cases_by_user(db: Session, user_id: str) -> int:
    """Count active cases for a user."""
    query = select(func.count(Case.id)).where(Case.user_id == user_id, Case.status == "active")
    return db.execute(query).scalar() or 0


def update_case(
    db: Session,
    *,
    db_case: Case,
    update_data: dict[str, Any],
) -> Case:
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
    from app.repositories.chat_file import create as create_chat_file

    chat_file = create_chat_file(
        db,
        user_id=user_id,
        filename=filename,
        mime_type=mime_type,
        size=size,
        storage_path=storage_path,
        file_type=file_type,
        parsed_content=parsed_content,
    )
    chat_file.case_id = case_id
    db.flush()
    db.refresh(chat_file)
    return chat_file


def get_documents_by_case(db: Session, case_id: str) -> list[ChatFile]:
    """Get all documents for a case."""
    query = select(ChatFile).where(ChatFile.case_id == case_id).order_by(ChatFile.created_at.desc())
    result = db.execute(query)
    return list(result.scalars().all())


def get_document_by_id(db: Session, doc_id: str) -> ChatFile | None:
    """Get a document by ID."""
    from app.repositories.chat_file import get_by_id

    return get_by_id(db, doc_id)


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
        .where(Conversation.is_archived.is_(False))
        .order_by(Conversation.updated_at.desc().nullslast(), Conversation.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = db.execute(query)
    return list(result.scalars().all())


def create_document_analysis(db: Session, *, chat_file_id: str) -> DocumentAnalysis:
    """Create a pending analysis record for a document."""
    analysis = DocumentAnalysis(chat_file_id=chat_file_id, status="pending")
    db.add(analysis)
    db.flush()
    db.refresh(analysis)
    return analysis


def update_document_analysis_status(
    db: Session,
    *,
    analysis_id: str,
    status: str,
    analysis_json: str | None = None,
    error_message: str | None = None,
) -> DocumentAnalysis | None:
    """Update analysis status and optionally store results."""
    from datetime import UTC, datetime

    analysis = db.get(DocumentAnalysis, analysis_id)
    if analysis:
        analysis.status = status
        if analysis_json is not None:
            analysis.analysis_json = analysis_json
        if error_message is not None:
            analysis.error_message = error_message
        if status == "completed":
            analysis.completed_at = datetime.now(UTC)
        db.flush()
        db.refresh(analysis)
    return analysis


def get_document_analysis(db: Session, doc_id: str) -> DocumentAnalysis | None:
    """Get analysis for a document by document ID."""
    query = select(DocumentAnalysis).where(DocumentAnalysis.chat_file_id == doc_id)
    result = db.execute(query)
    return result.scalar_one_or_none()


def get_analyses_by_case(db: Session, case_id: str) -> dict[str, DocumentAnalysis]:
    """Get all analysis records for documents in a case.

    Returns a dict mapping chat_file_id -> DocumentAnalysis.
    """
    query = (
        select(DocumentAnalysis)
        .join(ChatFile, DocumentAnalysis.chat_file_id == ChatFile.id)
        .where(ChatFile.case_id == case_id)
    )
    result = db.execute(query)
    return {a.chat_file_id: a for a in result.scalars().all()}


# Backward compatibility alias
LPACase = Case
