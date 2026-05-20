"""Tests for LPA Case repository functions."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.repositories import lpa_case_repo


@pytest.fixture
def mock_session():
    """Create a mock sync session."""
    session = MagicMock()
    return session


@pytest.fixture
def mock_case():
    """Create a mock LPACase instance."""
    case = MagicMock()
    case.id = "case-123"
    case.user_id = "user-123"
    case.name = "Test Case"
    case.description = "A test case"
    case.status = "active"
    case.created_at = datetime.now(UTC)
    case.updated_at = datetime.now(UTC)
    case.documents = []
    return case


@pytest.fixture
def mock_document():
    """Create a mock ChatFile instance."""
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
    doc.summary = "A summary"
    doc.created_at = datetime.now(UTC)
    return doc


class TestCreateCase:
    def test_create_case_success(self, mock_session, mock_case):
        mock_session.add = MagicMock()
        mock_session.flush = MagicMock()
        mock_session.refresh = MagicMock()

        with patch("app.repositories.lpa_case_repo.Case", return_value=mock_case):
            result = lpa_case_repo.create_case(
                mock_session, user_id="user-123", name="Test Case", description="desc"
            )

        mock_session.add.assert_called_once_with(mock_case)
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_case)
        assert result == mock_case

    def test_create_case_minimal(self, mock_session, mock_case):
        mock_session.add = MagicMock()
        mock_session.flush = MagicMock()
        mock_session.refresh = MagicMock()

        with patch("app.repositories.lpa_case_repo.Case", return_value=mock_case):
            result = lpa_case_repo.create_case(mock_session, user_id="user-123", name="Minimal")
        assert result == mock_case


class TestGetCaseById:
    def test_get_case_by_id_found(self, mock_session, mock_case):
        mock_session.get.return_value = mock_case
        result = lpa_case_repo.get_case_by_id(mock_session, "case-123")
        assert result == mock_case
        mock_session.get.assert_called_once()

    def test_get_case_by_id_not_found(self, mock_session):
        mock_session.get.return_value = None
        result = lpa_case_repo.get_case_by_id(mock_session, "nonexistent")
        assert result is None


class TestGetCaseByIdWithDocuments:
    def test_get_case_with_documents_found(self, mock_session, mock_case):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_case
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_case_by_id_with_documents(mock_session, "case-123")
        assert result == mock_case
        mock_session.execute.assert_called_once()

    def test_get_case_with_documents_not_found(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_case_by_id_with_documents(mock_session, "nonexistent")
        assert result is None


class TestGetCasesByUser:
    def test_get_cases_by_user_returns_tuples(self, mock_session, mock_case):
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_case, 3)]
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_cases_by_user(mock_session, "user-123")
        assert len(result) == 1
        assert result[0] == (mock_case, 3)

    def test_get_cases_by_user_with_pagination(self, mock_session, mock_case):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_cases_by_user(mock_session, "user-123", skip=10, limit=5)
        assert result == []
        mock_session.execute.assert_called_once()

    def test_get_cases_by_user_empty(self, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_cases_by_user(mock_session, "user-123")
        assert result == []


class TestCountCasesByUser:
    def test_count_cases_returns_int(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.count_cases_by_user(mock_session, "user-123")
        assert result == 5

    def test_count_cases_returns_zero_when_none(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.count_cases_by_user(mock_session, "user-123")
        assert result == 0


class TestUpdateCase:
    def test_update_case_applies_fields(self, mock_session, mock_case):
        mock_session.flush = MagicMock()
        mock_session.refresh = MagicMock()

        update_data = {"name": "Updated Name", "description": "New desc"}
        result = lpa_case_repo.update_case(mock_session, db_case=mock_case, update_data=update_data)

        assert mock_case.name == "Updated Name"
        assert mock_case.description == "New desc"
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_case)
        assert result == mock_case

    def test_update_case_empty_data(self, mock_session, mock_case):
        mock_session.flush = MagicMock()
        mock_session.refresh = MagicMock()

        result = lpa_case_repo.update_case(mock_session, db_case=mock_case, update_data={})
        mock_session.flush.assert_called_once()
        assert result == mock_case


class TestDeleteCase:
    def test_delete_case_success(self, mock_session, mock_case):
        mock_session.get.return_value = mock_case
        mock_session.delete = MagicMock()
        mock_session.flush = MagicMock()

        result = lpa_case_repo.delete_case(mock_session, "case-123")
        assert result is True
        mock_session.delete.assert_called_once_with(mock_case)
        mock_session.flush.assert_called_once()

    def test_delete_case_not_found(self, mock_session):
        mock_session.get.return_value = None

        result = lpa_case_repo.delete_case(mock_session, "nonexistent")
        assert result is False


class TestCreateDocument:
    def test_create_document_success(self, mock_session, mock_document):
        mock_session.add = MagicMock()
        mock_session.flush = MagicMock()
        mock_session.refresh = MagicMock()

        with patch("app.repositories.chat_file.ChatFile", return_value=mock_document):
            result = lpa_case_repo.create_document(
                mock_session,
                user_id="user-123",
                case_id="case-123",
                filename="test.pdf",
                mime_type="application/pdf",
                size=1024,
                storage_path="user-123/abc_test.pdf",
                file_type="pdf",
                parsed_content="text",
            )

        mock_session.add.assert_called_once()
        assert mock_session.flush.call_count == 2
        assert result == mock_document


class TestGetDocumentsByCase:
    def test_get_documents_returns_list(self, mock_session, mock_document):
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_document]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_documents_by_case(mock_session, "case-123")
        assert len(result) == 1
        assert result[0] == mock_document

    def test_get_documents_empty(self, mock_session):
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_documents_by_case(mock_session, "case-123")
        assert result == []


class TestGetDocumentById:
    def test_get_document_found(self, mock_session, mock_document):
        mock_session.get.return_value = mock_document
        result = lpa_case_repo.get_document_by_id(mock_session, "doc-123")
        assert result == mock_document

    def test_get_document_not_found(self, mock_session):
        mock_session.get.return_value = None
        result = lpa_case_repo.get_document_by_id(mock_session, "nonexistent")
        assert result is None


class TestDeleteDocument:
    def test_delete_document_success(self, mock_session, mock_document):
        mock_session.get.return_value = mock_document
        mock_session.delete = MagicMock()
        mock_session.flush = MagicMock()

        result = lpa_case_repo.delete_document(mock_session, "doc-123")
        assert result is True
        mock_session.delete.assert_called_once_with(mock_document)

    def test_delete_document_not_found(self, mock_session):
        mock_session.get.return_value = None
        result = lpa_case_repo.delete_document(mock_session, "nonexistent")
        assert result is False


class TestUpdateDocumentSummary:
    def test_update_document_summary_success(self, mock_session, mock_document):
        mock_session.get.return_value = mock_document
        mock_session.flush = MagicMock()
        mock_session.refresh = MagicMock()

        result = lpa_case_repo.update_document_summary(mock_session, "doc-123", "New summary")
        assert result == mock_document
        assert mock_document.summary == "New summary"
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_document)

    def test_update_document_summary_not_found(self, mock_session):
        mock_session.get.return_value = None
        result = lpa_case_repo.update_document_summary(mock_session, "nonexistent", "summary")
        assert result is None


class TestGetConversationsByCase:
    def test_get_conversations_returns_list(self, mock_session):
        mock_conv = MagicMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_conv]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_conversations_by_case(mock_session, "case-123")
        assert len(result) == 1
        assert result[0] == mock_conv

    def test_get_conversations_empty(self, mock_session):
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_conversations_by_case(mock_session, "case-123")
        assert result == []
