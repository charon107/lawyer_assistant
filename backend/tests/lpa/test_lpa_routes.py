"""Tests for LPA API routes."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.api.routes.v1.lpa import _get_chat_service, _get_lpa_service
from app.main import app


@pytest.fixture
def mock_lpa_service():
    """Mock LPAReviewService for route testing."""
    service = MagicMock()
    service.start_review = AsyncMock(return_value="test-review-123")
    service.get_status = MagicMock(
        return_value={
            "id": "test-review-123",
            "status": "complete",
            "filename": "test.pdf",
            "progress": 1.0,
            "progress_msg": "完成",
            "awaiting_chapter_confirmation": False,
            "chapters": None,
            "facts": None,
            "error": None,
        }
    )
    service.get_report = MagicMock(return_value="# Test Report")
    service.get_full_result = MagicMock(
        return_value={
            "id": "test-review-123",
            "status": "complete",
            "chapters": [],
            "chapter_reviews": [],
            "facts": {},
            "cross_check": {},
            "report_markdown": "# Test Report",
        }
    )
    service.confirm_chapters = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_chat_service():
    service = MagicMock()
    service.chat = AsyncMock(return_value="Test answer")
    return service


@pytest.fixture
def auth_headers(api_key_headers):
    """Headers with API key and a mock JWT token."""
    from app.core.security import create_access_token

    token = create_access_token(subject="test-user-id")
    return {**api_key_headers, "Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def clear_overrides():
    """Clear dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()


class TestStartReview:
    @pytest.mark.anyio
    async def test_start_review_success(self, client: AsyncClient, auth_headers, mock_lpa_service):
        app.dependency_overrides[_get_lpa_service] = lambda: mock_lpa_service
        response = await client.post(
            "/api/v1/lpa/review",
            files={"file": ("test.pdf", b"x" * 200, "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "review_id" in data
        assert data["status"] == "started"

    @pytest.mark.anyio
    async def test_start_review_no_filename(
        self, client: AsyncClient, auth_headers, mock_lpa_service
    ):
        app.dependency_overrides[_get_lpa_service] = lambda: mock_lpa_service
        response = await client.post(
            "/api/v1/lpa/review",
            files={"file": ("", b"x" * 200, "application/pdf")},
            headers=auth_headers,
        )
        # FastAPI returns 422 for validation errors on empty filename
        assert response.status_code in (400, 422)

    @pytest.mark.anyio
    async def test_start_review_unsupported_format(
        self, client: AsyncClient, auth_headers, mock_lpa_service
    ):
        app.dependency_overrides[_get_lpa_service] = lambda: mock_lpa_service
        response = await client.post(
            "/api/v1/lpa/review",
            files={"file": ("test.exe", b"x" * 200, "application/octet-stream")},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @pytest.mark.anyio
    async def test_start_review_file_too_short(
        self, client: AsyncClient, auth_headers, mock_lpa_service
    ):
        app.dependency_overrides[_get_lpa_service] = lambda: mock_lpa_service
        response = await client.post(
            "/api/v1/lpa/review",
            files={"file": ("test.pdf", b"short", "application/pdf")},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestGetReviewStatus:
    @pytest.mark.anyio
    async def test_get_status_success(self, client: AsyncClient, auth_headers, mock_lpa_service):
        app.dependency_overrides[_get_lpa_service] = lambda: mock_lpa_service
        response = await client.get(
            "/api/v1/lpa/review/test-review-123",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-review-123"
        assert data["status"] == "complete"

    @pytest.mark.anyio
    async def test_get_status_not_found(self, client: AsyncClient, auth_headers):
        service = MagicMock()
        service.get_status = MagicMock(return_value=None)
        app.dependency_overrides[_get_lpa_service] = lambda: service
        response = await client.get(
            "/api/v1/lpa/review/nonexistent",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGetReport:
    @pytest.mark.anyio
    async def test_get_report_success(self, client: AsyncClient, auth_headers, mock_lpa_service):
        app.dependency_overrides[_get_lpa_service] = lambda: mock_lpa_service
        response = await client.get(
            "/api/v1/lpa/review/test-review-123/report",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "report_markdown" in response.json()

    @pytest.mark.anyio
    async def test_get_report_not_ready(self, client: AsyncClient, auth_headers):
        service = MagicMock()
        service.get_report = MagicMock(return_value=None)
        app.dependency_overrides[_get_lpa_service] = lambda: service
        response = await client.get(
            "/api/v1/lpa/review/test-review-123/report",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGetFullResult:
    @pytest.mark.anyio
    async def test_get_full_result_success(
        self, client: AsyncClient, auth_headers, mock_lpa_service
    ):
        app.dependency_overrides[_get_lpa_service] = lambda: mock_lpa_service
        response = await client.get(
            "/api/v1/lpa/review/test-review-123/full",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-review-123"
        assert "report_markdown" in data


class TestConfirmChapters:
    @pytest.mark.anyio
    async def test_confirm_chapters_success(
        self, client: AsyncClient, auth_headers, mock_lpa_service
    ):
        app.dependency_overrides[_get_lpa_service] = lambda: mock_lpa_service
        response = await client.put(
            "/api/v1/lpa/review/test-review-123/chapters",
            json={"chapters": [{"index": 1, "title": "第一章", "text": "内容"}]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"


class TestChatFollowup:
    @pytest.mark.anyio
    async def test_chat_success(
        self, client: AsyncClient, auth_headers, mock_lpa_service, mock_chat_service
    ):
        app.dependency_overrides[_get_lpa_service] = lambda: mock_lpa_service
        app.dependency_overrides[_get_chat_service] = lambda: mock_chat_service
        response = await client.post(
            "/api/v1/lpa/review/test-review-123/chat",
            json={"question": "管理费率是多少?"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "answer" in response.json()

    @pytest.mark.anyio
    async def test_chat_review_not_found(self, client: AsyncClient, auth_headers):
        service = MagicMock()
        service.get_full_result = MagicMock(return_value=None)
        chat_service = MagicMock()
        app.dependency_overrides[_get_lpa_service] = lambda: service
        app.dependency_overrides[_get_chat_service] = lambda: chat_service
        response = await client.post(
            "/api/v1/lpa/review/nonexistent/chat",
            json={"question": "test"},
            headers=auth_headers,
        )
        assert response.status_code == 404
