"""Tests for user routes."""


from datetime import UTC, datetime
from unittest.mock import MagicMock

ServiceMock = MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import (
    get_current_active_superuser,
    get_current_user,
    get_db_session,
    get_system_log_service,
    get_user_service,
)
from app.core.config import settings
from app.main import app


class MockUser:
    """Mock user for testing."""

    def __init__(
        self,
        id=None,
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        role="user",
    ):
        self.id = id or str(uuid4())
        self.email = email
        self.full_name = full_name
        self.is_active = is_active
        self.role = role
        self.hashed_password = "hashed"
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def has_role(self, role) -> bool:
        """Check if user has the specified role."""
        if hasattr(role, "value"):
            return self.role == role.value
        return self.role == role


@pytest.fixture
def mock_user() -> MockUser:
    """Create a mock regular user."""
    return MockUser()


@pytest.fixture
def mock_superuser() -> MockUser:
    """Create a mock superuser."""
    return MockUser(role="admin", email="admin@example.com")


@pytest.fixture
def mock_user_service(mock_user: MockUser) -> MagicMock:
    """Create a mock user service."""
    service = MagicMock()
    service.get_by_id = MagicMock(return_value=mock_user)
    service.get_multi = MagicMock(return_value=[mock_user])
    service.admin_list = MagicMock(return_value=([mock_user], 1))
    service.update = MagicMock(return_value=mock_user)
    service.delete = MagicMock(return_value=mock_user)
    return service


@pytest.fixture
def mock_log_service() -> MagicMock:
    """Create a mock system log service that records calls."""
    service = MagicMock()
    service.log = MagicMock()
    return service


@pytest.fixture
async def auth_client(
    mock_user: MockUser,
    mock_user_service: MagicMock,
    mock_db_session,
) -> AsyncClient:
    """Client with authenticated regular user."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def superuser_client(
    mock_superuser: MockUser,
    mock_user_service: MagicMock,
    mock_log_service: MagicMock,
    mock_db_session,
) -> AsyncClient:
    """Client with authenticated superuser."""
    app.dependency_overrides[get_current_user] = lambda: mock_superuser
    app.dependency_overrides[get_current_active_superuser] = lambda: mock_superuser
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    app.dependency_overrides[get_system_log_service] = lambda: mock_log_service
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_read_current_user(auth_client: AsyncClient, mock_user: MockUser):
    """Test getting current user."""
    response = await auth_client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == mock_user.email


@pytest.mark.anyio
async def test_update_current_user(auth_client: AsyncClient, mock_user_service: MagicMock):
    """Test updating current user."""
    response = await auth_client.patch(
        f"{settings.API_V1_STR}/users/me",
        json={"full_name": "Updated Name"},
    )
    assert response.status_code == 200
    mock_user_service.update.assert_called_once()


@pytest.mark.anyio
async def test_read_users_superuser(superuser_client: AsyncClient, mock_user_service: MagicMock):
    """Test getting all users as superuser. Returns UserList with items and total."""
    response = await superuser_client.get(f"{settings.API_V1_STR}/users")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert data["total"] == 1


@pytest.mark.anyio
async def test_read_users_with_search(
    superuser_client: AsyncClient, mock_user_service: MagicMock
):
    """Search param is forwarded to the service."""
    response = await superuser_client.get(f"{settings.API_V1_STR}/users?search=foo")
    assert response.status_code == 200
    mock_user_service.admin_list.assert_called_once()
    call_kwargs = mock_user_service.admin_list.call_args.kwargs
    assert call_kwargs["search"] == "foo"


@pytest.mark.anyio
async def test_read_user_by_id(
    superuser_client: AsyncClient,
    mock_user: MockUser,
    mock_user_service: MagicMock,
):
    """Test getting user by ID as superuser."""
    response = await superuser_client.get(f"{settings.API_V1_STR}/users/{mock_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == mock_user.email


@pytest.mark.anyio
async def test_read_user_by_id_not_found(
    superuser_client: AsyncClient,
    mock_user_service: MagicMock,
):
    """Test getting non-existent user."""
    from app.core.exceptions import NotFoundError

    mock_user_service.get_by_id = ServiceMock(side_effect=NotFoundError(message="User not found"))

    response = await superuser_client.get(f"{settings.API_V1_STR}/users/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_user_by_id(
    superuser_client: AsyncClient,
    mock_user: MockUser,
    mock_user_service: MagicMock,
):
    """Test updating user by ID as superuser."""
    response = await superuser_client.patch(
        f"{settings.API_V1_STR}/users/{mock_user.id}",
        json={"full_name": "Admin Updated"},
    )
    assert response.status_code == 200
    mock_user_service.update.assert_called_once()


@pytest.mark.anyio
async def test_delete_user_by_id(
    superuser_client: AsyncClient,
    mock_user: MockUser,
    mock_user_service: MagicMock,
):
    """Test deleting user by ID as superuser."""
    response = await superuser_client.delete(f"{settings.API_V1_STR}/users/{mock_user.id}")
    assert response.status_code == 204
    mock_user_service.delete.assert_called_once()


@pytest.mark.anyio
async def test_delete_user_by_id_not_found(
    superuser_client: AsyncClient,
    mock_user_service: MagicMock,
):
    """Test deleting non-existent user."""
    from app.core.exceptions import NotFoundError

    mock_user_service.delete = ServiceMock(side_effect=NotFoundError(message="User not found"))

    response = await superuser_client.delete(f"{settings.API_V1_STR}/users/{uuid4()}")
    assert response.status_code == 404


# === Admin self-protection and audit logging ===


@pytest.mark.anyio
async def test_admin_cannot_demote_self(
    superuser_client: AsyncClient,
    mock_superuser: MockUser,
    mock_user_service: MagicMock,
):
    """Admin demoting their own role to 'user' is rejected."""
    response = await superuser_client.patch(
        f"{settings.API_V1_STR}/users/{mock_superuser.id}",
        json={"role": "user"},
    )
    assert response.status_code == 403
    mock_user_service.update.assert_not_called()


@pytest.mark.anyio
async def test_admin_cannot_disable_self(
    superuser_client: AsyncClient,
    mock_superuser: MockUser,
    mock_user_service: MagicMock,
):
    """Admin disabling their own account is rejected."""
    response = await superuser_client.patch(
        f"{settings.API_V1_STR}/users/{mock_superuser.id}",
        json={"is_active": False},
    )
    assert response.status_code == 403
    mock_user_service.update.assert_not_called()


@pytest.mark.anyio
async def test_admin_cannot_delete_self(
    superuser_client: AsyncClient,
    mock_superuser: MockUser,
    mock_user_service: MagicMock,
):
    """Admin deleting their own account is rejected."""
    response = await superuser_client.delete(
        f"{settings.API_V1_STR}/users/{mock_superuser.id}"
    )
    assert response.status_code == 403
    mock_user_service.delete.assert_not_called()


@pytest.mark.anyio
async def test_admin_role_change_logs_warning(
    superuser_client: AsyncClient,
    mock_user: MockUser,
    mock_log_service: MagicMock,
):
    """Promoting a user to admin writes a system_log at level=warning."""
    response = await superuser_client.patch(
        f"{settings.API_V1_STR}/users/{mock_user.id}",
        json={"role": "admin"},
    )
    assert response.status_code == 200
    mock_log_service.log.assert_called_once()
    args, kwargs = mock_log_service.log.call_args
    assert args[0] == "admin"
    assert args[1] == "update_user"
    assert kwargs["level"] == "warning"
    assert kwargs["resource_type"] == "user"
    assert kwargs["resource_id"] == mock_user.id
    assert "role" in kwargs["metadata"]
    assert kwargs["metadata"]["role"] == {"from": "user", "to": "admin"}


@pytest.mark.anyio
async def test_admin_field_only_change_logs_info(
    superuser_client: AsyncClient,
    mock_user: MockUser,
    mock_log_service: MagicMock,
):
    """Updating only full_name writes a system_log at level=info."""
    response = await superuser_client.patch(
        f"{settings.API_V1_STR}/users/{mock_user.id}",
        json={"full_name": "Renamed"},
    )
    assert response.status_code == 200
    mock_log_service.log.assert_called_once()
    kwargs = mock_log_service.log.call_args.kwargs
    assert kwargs["level"] == "info"
    assert "full_name" in kwargs["metadata"]


@pytest.mark.anyio
async def test_admin_password_reset_logs_redacted(
    superuser_client: AsyncClient,
    mock_user: MockUser,
    mock_log_service: MagicMock,
):
    """Password reset is logged as 'reset' without the password value."""
    response = await superuser_client.patch(
        f"{settings.API_V1_STR}/users/{mock_user.id}",
        json={"password": "newpassword123"},
    )
    assert response.status_code == 200
    kwargs = mock_log_service.log.call_args.kwargs
    assert kwargs["metadata"] == {"password": "reset"}


@pytest.mark.anyio
async def test_admin_unchanged_fields_skips_log(
    superuser_client: AsyncClient,
    mock_user: MockUser,
    mock_log_service: MagicMock,
):
    """If nothing actually changes, no audit log entry is written."""
    response = await superuser_client.patch(
        f"{settings.API_V1_STR}/users/{mock_user.id}",
        json={"full_name": mock_user.full_name},
    )
    assert response.status_code == 200
    mock_log_service.log.assert_not_called()


@pytest.mark.anyio
async def test_non_admin_cannot_patch_user(
    auth_client: AsyncClient,
    mock_user: MockUser,
):
    """Regular user calling admin PATCH endpoint is rejected."""
    other_id = str(uuid4())
    response = await auth_client.patch(
        f"{settings.API_V1_STR}/users/{other_id}",
        json={"role": "admin"},
    )
    assert response.status_code == 403
