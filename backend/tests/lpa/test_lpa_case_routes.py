"""Tests for LPA Cases API routes."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.api.deps import get_current_user, get_db_session
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app


@pytest.fixture
def mock_case():
    case = MagicMock()
    case.id = "case-123"
    case.user_id = "user-123"
    case.name = "Test Case"
    case.description = "A test case"
    case.status = "active"
    case.document_type = "lpa"
    case.documents = []
    case.created_at = datetime.now(UTC)
    case.updated_at = datetime.now(UTC)
    return case


@pytest.fixture
def mock_document():
    doc = MagicMock()
    doc.id = "doc-123"
    doc.filename = "test.pdf"
    doc.mime_type = "application/pdf"
    doc.file_type = "pdf"
    doc.size = 1024
    doc.summary = "summary"
    doc.parsed_content = "parsed"
    doc.created_at = datetime.now(UTC)
    return doc


@pytest.fixture
def mock_service(mock_case, mock_document):
    service = MagicMock()
    service.create.return_value = mock_case
    service.list.return_value = ([(mock_case, 3)], 1)
    service.get.return_value = mock_case
    service.get_without_docs.return_value = mock_case
    service.update.return_value = mock_case
    service.delete.return_value = True
    service.upload_document.return_value = mock_document
    service.get_documents.return_value = [mock_document]
    service.delete_document.return_value = True
    service.get_conversations.return_value = []
    return service


@pytest.fixture
def auth_headers():
    token = create_access_token(subject="user-123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _setup_overrides(mock_db_session, mock_user):
    """Set up standard dependency overrides for authenticated routes."""
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_user


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.is_active = True
    return user


# --- Case CRUD ---


class TestCreateCase:
    @pytest.mark.anyio
    async def test_create_case_success(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.post(
                f"{settings.API_V1_STR}/lpa-cases",
                json={"name": "Test Case", "description": "desc"},
                headers=auth_headers,
            )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Case"
        assert data["id"] == "case-123"
        assert data["document_count"] == 0

    @pytest.mark.anyio
    async def test_create_case_minimal(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.post(
                f"{settings.API_V1_STR}/lpa-cases",
                json={"name": "Minimal"},
                headers=auth_headers,
            )
        assert response.status_code == 201

    @pytest.mark.anyio
    async def test_create_case_unauthenticated(self, client: AsyncClient):
        response = await client.post(
            f"{settings.API_V1_STR}/lpa-cases",
            json={"name": "Test"},
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_create_case_empty_name(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.post(
                f"{settings.API_V1_STR}/lpa-cases",
                json={"name": ""},
                headers=auth_headers,
            )
        assert response.status_code == 422


class TestListCases:
    @pytest.mark.anyio
    async def test_list_cases_success(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.get(
                f"{settings.API_V1_STR}/lpa-cases",
                headers=auth_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["items"]) == 1

    @pytest.mark.anyio
    async def test_list_cases_with_pagination(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.get(
                f"{settings.API_V1_STR}/lpa-cases?skip=0&limit=10",
                headers=auth_headers,
            )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_list_cases_empty(
        self, client: AsyncClient, auth_headers, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        service = MagicMock()
        service.list.return_value = ([], 0)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=service):
            response = await client.get(
                f"{settings.API_V1_STR}/lpa-cases",
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestGetCase:
    @pytest.mark.anyio
    async def test_get_case_success(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.get(
                f"{settings.API_V1_STR}/lpa-cases/case-123",
                headers=auth_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "case-123"
        assert "documents" in data

    @pytest.mark.anyio
    async def test_get_case_not_found(
        self, client: AsyncClient, auth_headers, mock_db_session, mock_user
    ):
        from app.core.exceptions import NotFoundError

        _setup_overrides(mock_db_session, mock_user)
        service = MagicMock()
        service.get.side_effect = NotFoundError(message="Case not found")
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=service):
            response = await client.get(
                f"{settings.API_V1_STR}/lpa-cases/nonexistent",
                headers=auth_headers,
            )
        assert response.status_code == 404


class TestUpdateCase:
    @pytest.mark.anyio
    async def test_update_case_success(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.patch(
                f"{settings.API_V1_STR}/lpa-cases/case-123",
                json={"name": "Updated"},
                headers=auth_headers,
            )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_update_case_not_found(
        self, client: AsyncClient, auth_headers, mock_db_session, mock_user
    ):
        from app.core.exceptions import NotFoundError

        _setup_overrides(mock_db_session, mock_user)
        service = MagicMock()
        service.update.side_effect = NotFoundError(message="Case not found")
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=service):
            response = await client.patch(
                f"{settings.API_V1_STR}/lpa-cases/nonexistent",
                json={"name": "Updated"},
                headers=auth_headers,
            )
        assert response.status_code == 404


class TestDeleteCase:
    @pytest.mark.anyio
    async def test_delete_case_success(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.delete(
                f"{settings.API_V1_STR}/lpa-cases/case-123",
                headers=auth_headers,
            )
        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_delete_case_not_found(
        self, client: AsyncClient, auth_headers, mock_db_session, mock_user
    ):
        from app.core.exceptions import NotFoundError

        _setup_overrides(mock_db_session, mock_user)
        service = MagicMock()
        service.delete.side_effect = NotFoundError(message="Case not found")
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=service):
            response = await client.delete(
                f"{settings.API_V1_STR}/lpa-cases/nonexistent",
                headers=auth_headers,
            )
        assert response.status_code == 404


# --- Document operations ---


class TestUploadDocument:
    @pytest.mark.anyio
    async def test_upload_document_success(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        storage = MagicMock()
        storage.save = AsyncMock(return_value="user-123/abc_test.pdf")
        with (
            patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service),
            patch("app.services.file_storage.get_file_storage", return_value=storage),
            patch("app.api.routes.v1.lpa_cases._generate_summary_async"),
            patch("app.api.routes.v1.lpa_cases._generate_analysis_async"),
        ):
            response = await client.post(
                f"{settings.API_V1_STR}/lpa-cases/case-123/documents",
                files={"file": ("test.pdf", b"x" * 200, "application/pdf")},
                headers=auth_headers,
            )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.pdf"

    @pytest.mark.anyio
    async def test_upload_document_case_not_found(
        self, client: AsyncClient, auth_headers, mock_db_session, mock_user
    ):
        from app.core.exceptions import NotFoundError

        _setup_overrides(mock_db_session, mock_user)
        service = MagicMock()
        service.upload_document.side_effect = NotFoundError(message="Case not found")
        storage = MagicMock()
        storage.save = AsyncMock(return_value="path")
        with (
            patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=service),
            patch("app.services.file_storage.get_file_storage", return_value=storage),
        ):
            response = await client.post(
                f"{settings.API_V1_STR}/lpa-cases/nonexistent/documents",
                files={"file": ("test.pdf", b"x" * 200, "application/pdf")},
                headers=auth_headers,
            )
        assert response.status_code in (400, 404)


class TestListDocuments:
    @pytest.mark.anyio
    async def test_list_documents_success(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.get(
                f"{settings.API_V1_STR}/lpa-cases/case-123/documents",
                headers=auth_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 1


class TestDeleteDocument:
    @pytest.mark.anyio
    async def test_delete_document_success(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service):
            response = await client.delete(
                f"{settings.API_V1_STR}/lpa-cases/case-123/documents/doc-123",
                headers=auth_headers,
            )
        assert response.status_code == 204

    @pytest.mark.anyio
    async def test_delete_document_not_found(
        self, client: AsyncClient, auth_headers, mock_db_session, mock_user
    ):
        from app.core.exceptions import NotFoundError

        _setup_overrides(mock_db_session, mock_user)
        service = MagicMock()
        service.delete_document.side_effect = NotFoundError(message="Doc not found")
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=service):
            response = await client.delete(
                f"{settings.API_V1_STR}/lpa-cases/case-123/documents/nonexistent",
                headers=auth_headers,
            )
        assert response.status_code == 404


# --- Case conversations ---


class TestCaseConversations:
    @pytest.mark.anyio
    async def test_create_case_conversation_success(
        self, client: AsyncClient, auth_headers, mock_service, mock_db_session, mock_user
    ):
        _setup_overrides(mock_db_session, mock_user)
        mock_conv = MagicMock()
        mock_conv.id = "conv-123"
        mock_conv_service = MagicMock()
        mock_conv_service.create_conversation.return_value = mock_conv

        with (
            patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=mock_service),
            patch("app.services.conversation.ConversationService", return_value=mock_conv_service),
        ):
            response = await client.post(
                f"{settings.API_V1_STR}/lpa-cases/case-123/conversations",
                headers=auth_headers,
            )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "conv-123"
        assert data["case_id"] == "case-123"

    @pytest.mark.anyio
    async def test_create_case_conversation_case_not_found(
        self, client: AsyncClient, auth_headers, mock_db_session, mock_user
    ):
        from app.core.exceptions import NotFoundError

        _setup_overrides(mock_db_session, mock_user)
        service = MagicMock()
        service.get_without_docs.side_effect = NotFoundError(message="Case not found")
        with patch("app.api.routes.v1.lpa_cases.LPACaseService", return_value=service):
            response = await client.post(
                f"{settings.API_V1_STR}/lpa-cases/nonexistent/conversations",
                headers=auth_headers,
            )
        assert response.status_code == 404
