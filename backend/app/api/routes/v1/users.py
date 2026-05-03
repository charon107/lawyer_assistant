"""User management routes."""

from typing import Any

from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentAdmin,
    CurrentUser,
    UserSvc,
)
from app.db.models.user import UserRole
from app.schemas.user import UserRead, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: CurrentUser,
) -> Any:
    """Get current user.

    Returns the authenticated user's profile including their role.
    """
    return current_user


@router.patch("/me", response_model=UserRead)
def update_current_user(
    user_in: UserUpdate,
    current_user: CurrentUser,
    user_service: UserSvc,
) -> Any:
    """Update current user.

    Users can update their own profile (email, full_name).
    Role changes require admin privileges.
    """
    # Prevent non-admin users from changing their own role
    if user_in.role is not None and not current_user.has_role(UserRole.ADMIN):
        user_in.role = None
    user = user_service.update(current_user.id, user_in)
    return user


@router.get("", response_model=list[UserRead])
def read_users(
    user_service: UserSvc,
    _: CurrentAdmin,
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(100, ge=1, le=200, description="Max items to return"),
) -> Any:
    """Get all users (admin only)."""
    users = user_service.get_multi(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: str,
    user_service: UserSvc,
    _: CurrentAdmin,
) -> Any:
    """Get user by ID (admin only).

    Raises NotFoundError if user does not exist.
    """
    user = user_service.get_by_id(user_id)
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user_by_id(
    user_id: str,
    user_in: UserUpdate,
    user_service: UserSvc,
    _: CurrentAdmin,
) -> Any:
    """Update user by ID (admin only).

    Admins can update any user including their role.

    Raises NotFoundError if user does not exist.
    """
    user = user_service.update(user_id, user_in)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_user_by_id(
    user_id: str,
    user_service: UserSvc,
    _: CurrentAdmin,
) -> None:
    """Delete user by ID (admin only).

    Raises NotFoundError if user does not exist.
    """
    user_service.delete(user_id)
