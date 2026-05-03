"""Authentication routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, UserSvc
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserRead, UserRole

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserSvc,
) -> Any:
    """OAuth2 compatible token login.

    Returns access token and refresh token.
    Raises domain exceptions handled by exception handlers.
    """
    user = user_service.authenticate(form_data.username, form_data.password)
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    user_service: UserSvc,
) -> Any:
    """Register a new user.

    Raises AlreadyExistsError if email is already registered.
    """
    user = user_service.register(user_in)
    return UserRead(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=UserRole(user.role),
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    body: RefreshTokenRequest,
    user_service: UserSvc,
) -> Any:
    """Get new access token using refresh token.

    Raises AuthenticationError if refresh token is invalid or expired.
    """
    payload = verify_token(body.refresh_token)
    if payload is None:
        raise AuthenticationError(message="Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise AuthenticationError(message="Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError(message="Invalid token payload")

    # Verify user still exists and is active
    user = user_service.get_by_id(user_id)
    if not user.is_active:
        raise AuthenticationError(message="User account is disabled")

    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)
    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserRead)
def get_current_user_info(current_user: CurrentUser) -> Any:
    """Get current authenticated user information."""
    return UserRead(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        role=UserRole(current_user.role),
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
