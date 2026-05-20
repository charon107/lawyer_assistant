"""Authentication routes."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, SystemLogSvc, UserSvc
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserRead, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _rid(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserSvc,
    log_service: SystemLogSvc,
) -> Any:
    """OAuth2 compatible token login."""
    try:
        user = user_service.authenticate(form_data.username, form_data.password)
    except Exception:
        log_service.log(
            "auth",
            "login_failed",
            level="warning",
            metadata={"email": form_data.username},
            ip_address=_ip(request),
            request_id=_rid(request),
        )
        raise

    log_service.log(
        "auth",
        "login",
        user_id=str(user.id),
        ip_address=_ip(request),
        request_id=_rid(request),
    )
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    request: Request,
    user_in: UserCreate,
    user_service: UserSvc,
    log_service: SystemLogSvc,
) -> Any:
    """Register a new user."""
    user = user_service.register(user_in)
    log_service.log(
        "auth",
        "register",
        user_id=str(user.id),
        metadata={"email": user.email},
        ip_address=_ip(request),
        request_id=_rid(request),
    )
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
    """Get new access token using refresh token."""
    payload = verify_token(body.refresh_token)
    if payload is None:
        raise AuthenticationError(message="Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise AuthenticationError(message="Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError(message="Invalid token payload")

    user = user_service.get_by_id(user_id)
    if not user.is_active:
        raise AuthenticationError(message="User account is disabled")

    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)
    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def logout(
    request: Request,
    current_user: CurrentUser,
    log_service: SystemLogSvc,
) -> None:
    """Logout — log the event (tokens are stateless, no server-side invalidation)."""
    log_service.log(
        "auth",
        "logout",
        user_id=str(current_user.id),
        ip_address=_ip(request),
        request_id=_rid(request),
    )


@router.get("/me", response_model=UserRead)
def get_current_user_info(current_user: CurrentUser) -> Any:
    """Get current authenticated user information."""
    return current_user
