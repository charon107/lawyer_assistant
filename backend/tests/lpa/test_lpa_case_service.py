"""Tests for LPA Case service."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import BadRequestError, NotFoundError
from app.schemas.lpa_case import LPACaseCreate, LPACaseUpdate
from app.services.lpa_case_service import LPACaseService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return LPACaseService(mock_db)


@pytest.fixture
def mock_case():
    case = MagicMock()
    case.id = "case-123"
    case.user_id = "user-123"
    case.name = "Test Case"
    case.description = "desc"
    case.status = "active"
    case.documents = []
    case.created_at = datetime.now(UTC)
    case.updated_at = datetime.now(UTC)
    return case


@pytest.fixture
def mock_document():
    doc = MagicMock()
    doc.id = "doc-123"
    doc.user_id = "user-123"
    doc.case_id = "case-123"
    doc.filename = "test.pdf"
    doc.mime_type = "application/pdf"
    doc.file_type = "pdf"
    doc.size = 1024
    doc.storage_path = "user-123/abc_test.pdf"
    doc.parsed_content = "parsed text"
    doc.summary = None
    doc.created_at = datetime.now(UTC)
    return doc


class TestCreate:
    def test_create_success(self, service, mock_case):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.create_case.return_value = mock_case
            data = LPACaseCreate(name="Test Case", description="desc")
            result = service.create(data, user_id="user-123")
            assert result == mock_case
            mock_repo.create_case.assert_called_once()


class TestGet:
    def test_get_success(self, service, mock_case):
        mock_case.documents = []
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id_with_documents.return_value = mock_case
            result = service.get("case-123", user_id="user-123")
            assert result == mock_case

    def test_get_not_found(self, service):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id_with_documents.return_value = None
            with pytest.raises(NotFoundError):
                service.get("nonexistent", user_id="user-123")

    def test_get_wrong_user(self, service, mock_case):
        mock_case.user_id = "other-user"
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id_with_documents.return_value = mock_case
            with pytest.raises(NotFoundError):
                service.get("case-123", user_id="user-123")


class TestGetWithoutDocs:
    def test_get_without_docs_success(self, service, mock_case):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = mock_case
            result = service.get_without_docs("case-123", user_id="user-123")
            assert result == mock_case

    def test_get_without_docs_not_found(self, service):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = None
            with pytest.raises(NotFoundError):
                service.get_without_docs("nonexistent", user_id="user-123")


class TestList:
    def test_list_returns_items_and_total(self, service, mock_case):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_cases_by_user.return_value = [(mock_case, 3)]
            mock_repo.count_cases_by_user.return_value = 1
            items, total = service.list("user-123")
            assert len(items) == 1
            assert total == 1

    def test_list_empty(self, service):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_cases_by_user.return_value = []
            mock_repo.count_cases_by_user.return_value = 0
            items, total = service.list("user-123")
            assert items == []
            assert total == 0

    def test_list_with_pagination(self, service, mock_case):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_cases_by_user.return_value = [(mock_case, 1)]
            mock_repo.count_cases_by_user.return_value = 10
            items, total = service.list("user-123", skip=5, limit=5)
            mock_repo.get_cases_by_user.assert_called_once_with(
                mock_repo.get_cases_by_user.call_args[0][0],  # db
                "user-123",
                skip=5,
                limit=5,
            )


class TestUpdate:
    def test_update_success(self, service, mock_case):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = mock_case
            mock_repo.update_case.return_value = mock_case
            data = LPACaseUpdate(name="Updated")
            result = service.update("case-123", data, user_id="user-123")
            assert result == mock_case

    def test_update_no_changes(self, service, mock_case):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = mock_case
            data = LPACaseUpdate()  # no fields set
            result = service.update("case-123", data, user_id="user-123")
            assert result == mock_case
            mock_repo.update_case.assert_not_called()

    def test_update_not_found(self, service):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = None
            data = LPACaseUpdate(name="Updated")
            with pytest.raises(NotFoundError):
                service.update("nonexistent", data, user_id="user-123")


class TestDelete:
    def test_delete_success(self, service, mock_case):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = mock_case
            mock_repo.delete_case.return_value = True
            result = service.delete("case-123", user_id="user-123")
            assert result is True

    def test_delete_not_found(self, service):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = None
            with pytest.raises(NotFoundError):
                service.delete("nonexistent", user_id="user-123")


class TestUploadDocument:
    def test_upload_document_success(self, service, mock_case, mock_document):
        with (
            patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo,
            patch("app.services.file_upload.FileUploadService") as mock_file_svc_cls,
        ):
            mock_repo.get_case_by_id.return_value = mock_case
            mock_repo.create_document.return_value = mock_document

            mock_file_svc = MagicMock()
            mock_file_svc.validate_upload.return_value = (True, None)
            mock_file_svc.classify_file.return_value = "pdf"
            mock_file_svc.parse_content.return_value = "parsed"
            mock_file_svc_cls.return_value = mock_file_svc

            result = service.upload_document(
                "case-123",
                user_id="user-123",
                filename="test.pdf",
                mime_type="application/pdf",
                size=1024,
                data=b"file content",
                storage_path="user-123/abc_test.pdf",
            )
            assert result == mock_document

    def test_upload_document_invalid_type(self, service, mock_case):
        with (
            patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo,
            patch("app.services.file_upload.FileUploadService") as mock_file_svc_cls,
        ):
            mock_repo.get_case_by_id.return_value = mock_case
            mock_file_svc = MagicMock()
            mock_file_svc.validate_upload.return_value = (False, "Unsupported file type")
            mock_file_svc_cls.return_value = mock_file_svc

            with pytest.raises(BadRequestError):
                service.upload_document(
                    "case-123",
                    user_id="user-123",
                    filename="test.exe",
                    mime_type="application/octet-stream",
                    size=1024,
                    data=b"content",
                    storage_path="user-123/test.exe",
                )

    def test_upload_document_case_not_found(self, service):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = None
            with pytest.raises(NotFoundError):
                service.upload_document(
                    "nonexistent",
                    user_id="user-123",
                    filename="test.pdf",
                    mime_type="application/pdf",
                    size=1024,
                    data=b"content",
                    storage_path="path",
                )


class TestGetDocuments:
    def test_get_documents_success(self, service, mock_case, mock_document):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = mock_case
            mock_repo.get_documents_by_case.return_value = [mock_document]
            result = service.get_documents("case-123", user_id="user-123")
            assert len(result) == 1
            assert result[0] == mock_document

    def test_get_documents_case_not_found(self, service):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = None
            with pytest.raises(NotFoundError):
                service.get_documents("nonexistent", user_id="user-123")


class TestDeleteDocument:
    def test_delete_document_success(self, service, mock_case, mock_document):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = mock_case
            mock_repo.get_document_by_id.return_value = mock_document
            mock_repo.delete_document.return_value = True
            result = service.delete_document("case-123", "doc-123", user_id="user-123")
            assert result is True

    def test_delete_document_not_found(self, service, mock_case):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = mock_case
            mock_repo.get_document_by_id.return_value = None
            with pytest.raises(NotFoundError):
                service.delete_document("case-123", "nonexistent", user_id="user-123")

    def test_delete_document_wrong_case(self, service, mock_case, mock_document):
        mock_document.case_id = "other-case"
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = mock_case
            mock_repo.get_document_by_id.return_value = mock_document
            with pytest.raises(NotFoundError):
                service.delete_document("case-123", "doc-123", user_id="user-123")

    def test_delete_document_case_not_found(self, service):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = None
            with pytest.raises(NotFoundError):
                service.delete_document("nonexistent", "doc-123", user_id="user-123")


class TestGetConversations:
    def test_get_conversations_success(self, service, mock_case):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = mock_case
            mock_conv = MagicMock()
            mock_repo.get_conversations_by_case.return_value = [mock_conv]
            result = service.get_conversations("case-123", user_id="user-123")
            assert len(result) == 1

    def test_get_conversations_case_not_found(self, service):
        with patch("app.services.lpa_case_service.lpa_case_repo") as mock_repo:
            mock_repo.get_case_by_id.return_value = None
            with pytest.raises(NotFoundError):
                service.get_conversations("nonexistent", user_id="user-123")
