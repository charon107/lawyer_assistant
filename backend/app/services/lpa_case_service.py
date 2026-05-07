"""LPA Case service (SQLite sync)."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.chat_file import ChatFile
from app.db.models.lpa_case import LPACase
from app.repositories import lpa_case_repo
from app.schemas.lpa_case import LPACaseCreate, LPACaseUpdate

logger = logging.getLogger(__name__)


class LPACaseService:
    """Service for LPA case business logic."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: LPACaseCreate, user_id: str) -> LPACase:
        """Create a new LPA case."""
        return lpa_case_repo.create_case(
            self.db, user_id=user_id, name=data.name, description=data.description
        )

    def get(self, case_id: str, user_id: str) -> LPACase:
        """Get an LPA case by ID with documents.

        Raises:
            NotFoundError: If case does not exist or user has no access.
        """
        case = lpa_case_repo.get_case_by_id_with_documents(self.db, case_id)
        if not case or str(case.user_id) != str(user_id):
            raise NotFoundError(message="Case not found", details={"case_id": case_id})
        return case

    def get_without_docs(self, case_id: str, user_id: str) -> LPACase:
        """Get an LPA case by ID without documents.

        Raises:
            NotFoundError: If case does not exist or user has no access.
        """
        case = lpa_case_repo.get_case_by_id(self.db, case_id)
        if not case or str(case.user_id) != str(user_id):
            raise NotFoundError(message="Case not found", details={"case_id": case_id})
        return case

    def list(
        self, user_id: str, *, skip: int = 0, limit: int = 50
    ) -> tuple[list[tuple[LPACase, int]], int]:
        """List LPA cases with document count.

        Returns:
            Tuple of (cases_with_count, total).
        """
        items = lpa_case_repo.get_cases_by_user(self.db, user_id, skip=skip, limit=limit)
        total = lpa_case_repo.count_cases_by_user(self.db, user_id)
        return items, total

    def update(self, case_id: str, data: LPACaseUpdate, user_id: str) -> LPACase:
        """Update an LPA case.

        Raises:
            NotFoundError: If case does not exist or user has no access.
        """
        case = self.get_without_docs(case_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return case
        return lpa_case_repo.update_case(self.db, db_case=case, update_data=update_data)

    def delete(self, case_id: str, user_id: str) -> bool:
        """Delete an LPA case (cascades to documents and conversations).

        Raises:
            NotFoundError: If case does not exist or user has no access.
        """
        self.get_without_docs(case_id, user_id)
        return lpa_case_repo.delete_case(self.db, case_id)

    def upload_document(
        self,
        case_id: str,
        user_id: str,
        *,
        filename: str,
        mime_type: str,
        size: int,
        data: bytes,
        storage_path: str,
    ) -> ChatFile:
        """Upload a document to a case.

        The caller is responsible for saving the file to storage first
        (via get_file_storage().save()) and passing the resulting storage_path.

        Raises:
            NotFoundError: If case does not exist.
            BadRequestError: If file type is not supported.
        """
        from app.core.exceptions import BadRequestError
        from app.services.file_upload import FileUploadService

        # Verify case ownership
        self.get_without_docs(case_id, user_id)

        # Validate upload
        file_service = FileUploadService(self.db)
        is_valid, error_msg = file_service.validate_upload(mime_type, size)
        if not is_valid:
            raise BadRequestError(message=error_msg or "Invalid file")

        # Classify and parse
        file_type = file_service.classify_file(mime_type, filename)
        parsed_content = file_service.parse_content(data, file_type, mime_type)

        # Create record
        doc = lpa_case_repo.create_document(
            self.db,
            user_id=user_id,
            case_id=case_id,
            filename=filename,
            mime_type=mime_type,
            size=size,
            storage_path=storage_path,
            file_type=file_type,
            parsed_content=parsed_content,
        )

        return doc

    def get_documents(self, case_id: str, user_id: str) -> list[ChatFile]:
        """Get all documents for a case.

        Raises:
            NotFoundError: If case does not exist or user has no access.
        """
        self.get_without_docs(case_id, user_id)
        return lpa_case_repo.get_documents_by_case(self.db, case_id)

    def delete_document(self, case_id: str, doc_id: str, user_id: str) -> bool:
        """Delete a document from a case.

        Raises:
            NotFoundError: If case or document does not exist.
        """
        self.get_without_docs(case_id, user_id)
        doc = lpa_case_repo.get_document_by_id(self.db, doc_id)
        if not doc or str(doc.case_id) != str(case_id):
            raise NotFoundError(message="Document not found", details={"doc_id": doc_id})
        return lpa_case_repo.delete_document(self.db, doc_id)

    def get_conversations(
        self, case_id: str, user_id: str, *, skip: int = 0, limit: int = 50
    ) -> list[Any]:
        """Get conversations for a case.

        Raises:
            NotFoundError: If case does not exist or user has no access.
        """
        self.get_without_docs(case_id, user_id)
        return lpa_case_repo.get_conversations_by_case(self.db, case_id, skip=skip, limit=limit)
