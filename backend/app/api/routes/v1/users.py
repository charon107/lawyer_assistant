"""User management routes."""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentAdmin,
    CurrentUser,
    DBSession,
    UserSvc,
)
from app.db.models.user import UserRole
from app.db.models.user_llm_config import UserLLMConfig
from app.schemas.user import (
    LLMConfigCreate,
    LLMConfigRead,
    LLMConfigUpdate,
    UserRead,
    UserUpdate,
)

logger = logging.getLogger(__name__)

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


# === LLM Config CRUD ===


@router.get("/me/llm-configs", response_model=list[LLMConfigRead])
def list_llm_configs(
    current_user: CurrentUser,
    db: DBSession,
) -> Any:
    """List all LLM provider configs for the current user."""
    from sqlalchemy import select

    result = db.execute(select(UserLLMConfig).where(UserLLMConfig.user_id == current_user.id))
    configs = result.scalars().all()
    return configs


@router.post("/me/llm-configs", response_model=LLMConfigRead, status_code=status.HTTP_201_CREATED)
def create_llm_config(
    config_in: LLMConfigCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> Any:
    """Create a new LLM provider config."""
    config = UserLLMConfig(
        user_id=current_user.id,
        provider=config_in.provider,
        model=config_in.model,
        api_key=config_in.api_key,
        base_url=config_in.base_url,
    )
    db.add(config)
    db.flush()
    db.refresh(config)
    return config


@router.patch("/me/llm-configs/{config_id}", response_model=LLMConfigRead)
def update_llm_config(
    config_id: str,
    config_in: LLMConfigUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> Any:
    """Update an LLM provider config."""
    from sqlalchemy import select

    result = db.execute(
        select(UserLLMConfig).where(
            UserLLMConfig.id == config_id,
            UserLLMConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(message="配置不存在", details={"config_id": config_id})

    update_data = config_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    db.flush()
    db.refresh(config)
    return config


@router.delete(
    "/me/llm-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None
)
def delete_llm_config(
    config_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete an LLM provider config."""
    from sqlalchemy import select

    result = db.execute(
        select(UserLLMConfig).where(
            UserLLMConfig.id == config_id,
            UserLLMConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        from app.core.exceptions import NotFoundError

        raise NotFoundError(message="配置不存在", details={"config_id": config_id})
    db.delete(config)
    db.flush()


@router.post("/me/llm-configs/{config_id}/test-connection")
def test_llm_connection(
    config_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> dict[str, Any]:
    """Test a specific LLM provider connection and return available models.

    Returns {success: bool, message: str, models: list[str]}.
    """
    from sqlalchemy import select

    result = db.execute(
        select(UserLLMConfig).where(
            UserLLMConfig.id == config_id,
            UserLLMConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        return {"success": False, "message": "配置不存在", "models": []}

    if not config.api_key:
        return {"success": False, "message": "请先配置 API Key", "models": []}

    try:
        if config.provider == "anthropic":
            test_result = _test_anthropic(config.api_key, config.base_url)
        elif config.provider == "google":
            test_result = _test_google(config.api_key, config.base_url)
        else:
            test_result = _test_openai_compatible(config.api_key, config.base_url)

        # If test succeeded, also fetch available models
        if test_result["success"]:
            models_result = _fetch_models(config.provider, config.api_key, config.base_url)
            test_result["models"] = models_result.get("models", [])
        else:
            test_result["models"] = []

        return test_result
    except Exception as e:
        logger.warning("LLM connection test failed: %s", e)
        return {"success": False, "message": f"连接失败: {str(e)[:200]}", "models": []}


@router.post("/me/llm-configs/{config_id}/list-models")
def list_config_models(
    config_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> dict[str, Any]:
    """Fetch available models for a specific LLM provider config.

    Returns {models: list[str]}.
    """
    from sqlalchemy import select

    result = db.execute(
        select(UserLLMConfig).where(
            UserLLMConfig.id == config_id,
            UserLLMConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()
    if not config or not config.api_key:
        return {"models": []}

    return _fetch_models(config.provider, config.api_key, config.base_url)


# === Helper functions ===


def _test_openai_compatible(api_key: str, base_url: str | None) -> dict[str, Any]:
    """Test OpenAI-compatible provider via GET /models."""
    url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/models"
    resp = httpx.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
    if resp.status_code == 200:
        return {"success": True, "message": "连接成功"}
    return {"success": False, "message": f"连接失败 (HTTP {resp.status_code})"}


def _test_anthropic(api_key: str, base_url: str | None) -> dict[str, Any]:
    """Test Anthropic provider via POST /v1/messages with minimal request."""
    url = (base_url or "https://api.anthropic.com").rstrip("/") + "/v1/messages"
    resp = httpx.post(
        url,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "hi"}],
        },
        timeout=15,
    )
    if resp.status_code == 200:
        return {"success": True, "message": "连接成功"}
    if resp.status_code == 401:
        return {"success": False, "message": "API Key 无效"}
    if resp.status_code == 400:
        return {"success": True, "message": "连接成功"}
    return {"success": False, "message": f"连接失败 (HTTP {resp.status_code})"}


def _test_google(api_key: str, base_url: str | None) -> dict[str, Any]:
    """Test Google AI Studio via GET /models?key=..."""
    url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/") + "/models"
    resp = httpx.get(url, params={"key": api_key}, timeout=10)
    if resp.status_code == 200:
        return {"success": True, "message": "连接成功"}
    if resp.status_code in (400, 401, 403):
        return {"success": False, "message": "API Key 无效"}
    return {"success": False, "message": f"连接失败 (HTTP {resp.status_code})"}


def _fetch_models(provider: str, api_key: str, base_url: str | None) -> dict[str, Any]:
    """Fetch available models from a provider's API."""
    if provider == "anthropic":
        return {"models": ["claude-opus-4-7", "claude-sonnet-4-6", "claude-haiku-4-5"]}

    if provider == "google":
        try:
            url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip(
                "/"
            ) + "/models"
            resp = httpx.get(url, params={"key": api_key}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "models": sorted([m["name"].split("/")[-1] for m in data.get("models", [])])
                }
        except Exception as e:
            logger.warning("Failed to fetch Google models: %s", e)
        return {"models": []}

    try:
        url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/models"
        resp = httpx.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"models": sorted([m["id"] for m in data.get("data", [])])}
    except Exception as e:
        logger.warning("Failed to fetch models: %s", e)
    return {"models": []}


# === Admin endpoints ===


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
