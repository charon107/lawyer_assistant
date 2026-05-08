"""User schemas."""

from enum import StrEnum
from typing import Any

from pydantic import EmailStr, Field, field_validator, model_validator

from app.schemas.base import BaseSchema, TimestampSchema

# === LLM Config schemas ===


class LLMConfigCreate(BaseSchema):
    """Schema for creating an LLM provider config."""

    provider: str = Field(max_length=50)
    model: str | None = Field(default=None, max_length=100)
    api_key: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=500)


class LLMConfigUpdate(BaseSchema):
    """Schema for updating an LLM provider config."""

    provider: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=100)
    api_key: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=500)


class LLMConfigRead(BaseSchema):
    """Schema for reading an LLM provider config."""

    id: str
    provider: str
    model: str | None = None
    base_url: str | None = None
    has_api_key: bool = False

    @model_validator(mode="before")
    @classmethod
    def compute_key_flag(cls, data: Any) -> Any:
        if hasattr(data, "api_key"):
            flag = {"has_api_key": bool(data.api_key)}
            if isinstance(data, dict):
                data.update(flag)
            else:
                for k, v in flag.items():
                    setattr(data, k, v)
        return data


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

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        return v.lower() if v is not None else None


class UserRead(UserBase, TimestampSchema):
    """Schema for reading a user."""

    id: str
    role: UserRole = UserRole.USER
    avatar_url: str | None = None
    llm_configs: list[LLMConfigRead] = []

    @model_validator(mode="before")
    @classmethod
    def compute_llm_configs(cls, data: Any) -> Any:
        if hasattr(data, "llm_configs"):
            configs = []
            for cfg in data.llm_configs:
                configs.append(LLMConfigRead(
                    id=cfg.id,
                    provider=cfg.provider,
                    model=cfg.model,
                    base_url=cfg.base_url,
                    has_api_key=bool(cfg.api_key),
                ))
            if isinstance(data, dict):
                data["llm_configs"] = configs
            else:
                # Convert ORM object to dict to avoid SQLAlchemy relationship conflict
                data_dict = {k: v for k, v in data.__dict__.items() if not k.startswith("_")}
                data_dict["llm_configs"] = configs
                return data_dict
        return data


class UserInDB(UserRead):
    """User schema with hashed password (internal use)."""

    hashed_password: str
