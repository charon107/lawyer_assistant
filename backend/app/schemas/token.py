"""Token schemas."""

from pydantic import BaseModel


class Token(BaseModel):
    """OAuth2 token response with refresh token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str
