"""User schemas."""

from enum import StrEnum
from typing import Any

from pydantic import EmailStr, Field, field_validator, model_validator

from app.schemas.base import BaseSchema, TimestampSchema


class UserRole(StrEnum):
    """User role enumeration for API schemas."""

    ADMIN = "admin"
    USER = "user"


class UserBase(BaseSchema):
    """Base user schema."""

    email: EmailStr = Field(max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()


class UserCreate(BaseSchema):
    """Schema for creating a user."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = UserRole.USER

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower()


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    role: UserRole | None = None
    llm_provider: str | None = Field(default=None, max_length=50)
    ai_model: str | None = Field(default=None, max_length=100)
    openai_api_key: str | None = Field(default=None, max_length=255)
    anthropic_api_key: str | None = Field(default=None, max_length=255)
    llm_base_url: str | None = Field(default=None, max_length=500)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        return v.lower() if v is not None else None


class UserRead(UserBase, TimestampSchema):
    """Schema for reading a user."""

    id: str
    role: UserRole = UserRole.USER
    avatar_url: str | None = None
    llm_provider: str | None = None
    ai_model: str | None = None
    llm_base_url: str | None = None
    has_openai_key: bool = False
    has_anthropic_key: bool = False

    @model_validator(mode="before")
    @classmethod
    def compute_api_key_flags(cls, data: Any) -> Any:
        if hasattr(data, "openai_api_key"):
            data_has = {
                "has_openai_key": bool(data.openai_api_key),
                "has_anthropic_key": bool(data.anthropic_api_key),
            }
            if isinstance(data, dict):
                data.update(data_has)
            else:
                for k, v in data_has.items():
                    setattr(data, k, v)
        return data


class UserInDB(UserRead):
    """User schema with hashed password (internal use)."""

    hashed_password: str
