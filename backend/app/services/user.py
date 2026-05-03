"""User service (SQLite sync).

Contains business logic for user operations. Uses UserRepository for database access.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from app.core.exceptions import AlreadyExistsError, AuthenticationError, NotFoundError
from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserCreate, UserUpdate

if TYPE_CHECKING:
    from app.schemas.conversation_share import AdminUserList


class UserService:
    """Service for user-related business logic."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> User:
        """Get user by ID.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = user_repo.get_by_id(self.db, user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": user_id},
            )
        return user

    def get_by_email(self, email: str) -> User | None:
        """Get user by email. Returns None if not found."""
        return user_repo.get_by_email(self.db, email)

    def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Get multiple users with pagination."""
        return user_repo.get_multi(self.db, skip=skip, limit=limit)

    def list_paginated(self) -> Any:
        """Return paginated user list (fastapi-pagination Page)."""
        from fastapi_pagination.ext.sqlalchemy import paginate

        return paginate(self.db, user_repo.list_query())

    def delete_non_admins(self) -> int:
        """Bulk-delete users without the admin role. Returns affected row count."""
        return user_repo.delete_non_admins(self.db)

    def has_any(self) -> bool:
        """Return True if at least one user exists."""
        return user_repo.has_any(self.db)

    def admin_list_with_counts(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> "AdminUserList":
        """Admin: list users with conversation counts."""
        from app.schemas.conversation_share import AdminUserList, AdminUserRead

        rows, total = user_repo.admin_list_with_counts(
            self.db,
            skip=skip,
            limit=limit,
            search=search,
        )
        items = [
            AdminUserRead(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                conversation_count=conv_count,
                created_at=user.created_at,
            )
            for user, conv_count in rows
        ]
        return AdminUserList(items=items, total=total)

    def register(self, user_in: UserCreate) -> User:
        """Register a new user.

        Raises:
            AlreadyExistsError: If email is already registered.
        """
        existing = user_repo.get_by_email(self.db, user_in.email)
        if existing:
            raise AlreadyExistsError(
                message="Email already registered",
                details={"email": user_in.email},
            )

        hashed_password = get_password_hash(user_in.password)
        return user_repo.create(
            self.db,
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role.value,
        )

    def authenticate(self, email: str, password: str) -> User:
        """Authenticate user by email and password.

        Raises:
            AuthenticationError: If credentials are invalid or user is inactive.
        """
        user = user_repo.get_by_email(self.db, email)
        if (
            not user
            or not user.hashed_password
            or not verify_password(password, user.hashed_password)
        ):
            raise AuthenticationError(message="Invalid email or password")
        if not user.is_active:
            raise AuthenticationError(message="User account is disabled")
        return user

    def update(self, user_id: str, user_in: UserUpdate) -> User:
        """Update user.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = self.get_by_id(user_id)

        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        return user_repo.update(self.db, db_user=user, update_data=update_data)

    def delete(self, user_id: str) -> User:
        """Delete user.

        Raises:
            NotFoundError: If user does not exist.
        """
        user = user_repo.delete(self.db, user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": user_id},
            )
        return user
