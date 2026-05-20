"""LPA Cases API routes."""

import logging
from typing import Any

from fastapi import APIRouter, File, Query, UploadFile, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.document_analysis import DocumentAnalysisRead
from app.schemas.lpa_case import (
    CaseCreate,
    CaseDetailRead,
    CaseList,
    CaseRead,
    CaseUpdate,
    DocumentList,
    DocumentRead,
)
from app.services.lpa_analysis_service import (
    schedule_analysis_generation,
    schedule_summary_generation,
)
from app.services.lpa_case_service import CaseService

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_service(db: DBSession) -> CaseService:
    return CaseService(db)


# --- Case CRUD ---


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CaseCreate,
    db: DBSession,
    user: CurrentUser,
) -> Any:
    """Create a new LPA case."""
    service = _get_service(db)
    case = service.create(data, user_id=str(user.id))
    return CaseRead(
        id=case.id,
        user_id=case.user_id,
        name=case.name,
        description=case.description,
        status=case.status,
        document_type=case.document_type,
        document_count=0,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.get("", response_model=CaseList)
async def list_cases(
    db: DBSession,
    user: CurrentUser,
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max items to return"),
) -> Any:
    """List LPA cases with document counts."""
    service = _get_service(db)
    items, total = service.list(str(user.id), skip=skip, limit=limit)
    case_reads = [
        CaseRead(
            id=case.id,
            user_id=case.user_id,
            name=case.name,
            description=case.description,
            status=case.status,
            document_type=case.document_type,
            document_count=doc_count,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )
        for case, doc_count in items
    ]
    return CaseList(items=case_reads, total=total)


@router.get("/{case_id}", response_model=CaseDetailRead)
async def get_case(
    case_id: str,
    db: DBSession,
    user: CurrentUser,
) -> Any:
    """Get LPA case details with documents."""
    service = _get_service(db)
    case = service.get(case_id, user_id=str(user.id))
    analyses = service.get_analyses_by_case(case_id, user_id=str(user.id))
    documents = [
        DocumentRead(
            id=doc.id,
            filename=doc.filename,
            mime_type=doc.mime_type,
            file_type=doc.file_type,
            size=doc.size,
            summary=doc.summary,
            has_parsed_content=bool(doc.parsed_content),
            analysis_status=analyses[doc.id].status if doc.id in analyses else None,
            created_at=doc.created_at,
        )
        for doc in case.documents
    ]
    return CaseDetailRead(
        id=case.id,
        user_id=case.user_id,
        name=case.name,
        description=case.description,
        status=case.status,
        document_type=case.document_type,
        document_count=len(documents),
        documents=documents,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.patch("/{case_id}", response_model=CaseRead)
async def update_case(
    case_id: str,
    data: CaseUpdate,
    db: DBSession,
    user: CurrentUser,
) -> Any:
    """Update an LPA case."""
    service = _get_service(db)
    case = service.update(case_id, data, user_id=str(user.id))
    doc_count = len(case.documents) if hasattr(case, "documents") and case.documents else 0
    return CaseRead(
        id=case.id,
        user_id=case.user_id,
        name=case.name,
        description=case.description,
        status=case.status,
        document_type=case.document_type,
        document_count=doc_count,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_case(
    case_id: str,
    db: DBSession,
    user: CurrentUser,
) -> None:
    """Delete an LPA case (cascades to documents and conversations)."""
    service = _get_service(db)
    service.delete(case_id, user_id=str(user.id))


# --- Document operations ---


@router.post(
    "/{case_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    case_id: str,
    db: DBSession,
    user: CurrentUser,
    file: UploadFile = File(...),
) -> Any:
    """Upload a document to an LPA case."""
    from app.services.file_storage import get_file_storage

    service = _get_service(db)
    data = await file.read()
    filename = file.filename or "document"

    # Save file to storage (async)
    storage = get_file_storage()
    storage_path = await storage.save(str(user.id), filename, data)

    doc = service.upload_document(
        case_id,
        user_id=str(user.id),
        filename=filename,
        mime_type=file.content_type or "application/octet-stream",
        size=len(data),
        data=data,
        storage_path=storage_path,
    )

    # Generate summary and analysis asynchronously (extract values before task to avoid detached instance)
    schedule_summary_generation(doc.id, doc.parsed_content)
    schedule_analysis_generation(doc.id, doc.parsed_content)

    return DocumentRead(
        id=doc.id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        file_type=doc.file_type,
        size=doc.size,
        summary=doc.summary,
        has_parsed_content=bool(doc.parsed_content),
        created_at=doc.created_at,
    )


@router.get("/{case_id}/documents", response_model=DocumentList)
async def list_documents(
    case_id: str,
    db: DBSession,
    user: CurrentUser,
) -> Any:
    """List documents for an LPA case."""
    service = _get_service(db)
    documents = service.get_documents(case_id, user_id=str(user.id))
    analyses = service.get_analyses_by_case(case_id, user_id=str(user.id))
    items = [
        DocumentRead(
            id=doc.id,
            filename=doc.filename,
            mime_type=doc.mime_type,
            file_type=doc.file_type,
            size=doc.size,
            summary=doc.summary,
            has_parsed_content=bool(doc.parsed_content),
            analysis_status=analyses[doc.id].status if doc.id in analyses else None,
            created_at=doc.created_at,
        )
        for doc in documents
    ]
    return DocumentList(items=items, total=len(items))


@router.delete(
    "/{case_id}/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_document(
    case_id: str,
    doc_id: str,
    db: DBSession,
    user: CurrentUser,
) -> None:
    """Delete a document from an LPA case."""
    service = _get_service(db)
    service.delete_document(case_id, doc_id, user_id=str(user.id))


@router.get("/{case_id}/documents/{doc_id}/analysis", response_model=DocumentAnalysisRead)
async def get_document_analysis(
    case_id: str,
    doc_id: str,
    db: DBSession,
    user: CurrentUser,
) -> Any:
    """Get the pre-analysis result for a document."""
    service = _get_service(db)
    analysis = service.get_document_analysis(case_id, doc_id, user_id=str(user.id))
    if not analysis:
        from app.schemas.document_analysis import DocumentAnalysisResult

        return DocumentAnalysisRead(
            id="",
            chat_file_id=doc_id,
            status="not_found",
        )
    parsed = None
    if analysis.status == "completed" and analysis.analysis_json:
        from app.schemas.document_analysis import DocumentAnalysisResult

        parsed = DocumentAnalysisResult.model_validate_json(analysis.analysis_json)
    return DocumentAnalysisRead(
        id=analysis.id,
        chat_file_id=analysis.chat_file_id,
        status=analysis.status,
        analysis=parsed,
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
    )


# --- Case conversations ---


@router.post("/{case_id}/conversations", status_code=status.HTTP_201_CREATED)
async def create_case_conversation(
    case_id: str,
    db: DBSession,
    user: CurrentUser,
) -> Any:
    """Create a new conversation for an LPA case."""
    from app.schemas.conversation import ConversationCreate

    service = _get_service(db)
    # Verify case ownership
    service.get_without_docs(case_id, user_id=str(user.id))

    from app.services.conversation import ConversationService

    conv_service = ConversationService(db)
    conv_data = ConversationCreate(user_id=str(user.id), case_id=case_id)
    conversation = conv_service.create_conversation(conv_data)
    return {"id": conversation.id, "case_id": case_id}
