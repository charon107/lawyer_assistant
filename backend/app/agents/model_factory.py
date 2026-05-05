"""Model factory — creates PydanticAI models for OpenAI-compatible or Anthropic providers."""

import logging
from typing import Any

from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider

from app.core.config import settings

logger = logging.getLogger(__name__)


def create_pydantic_model(
    provider: str | None = None,
    model_name: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAIModel | AnthropicModel:
    """Create a PydanticAI model based on provider configuration.

    Args:
        provider: "openai", "anthropic", "google", etc. Defaults to settings.LLM_PROVIDER.
        model_name: Model name. Defaults to settings.AI_MODEL.
        api_key: API key for the provider. Defaults to settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY.
        base_url: Custom base URL for OpenAI-compatible APIs. Defaults to settings.LLM_BASE_URL.

    Returns:
        OpenAIModel or AnthropicModel instance.
    """
    provider = provider or settings.LLM_PROVIDER
    model_name = model_name or settings.AI_MODEL
    api_key = api_key or (settings.ANTHROPIC_API_KEY if provider == "anthropic" else settings.OPENAI_API_KEY)
    base_url = base_url or settings.LLM_BASE_URL

    if provider == "anthropic":
        logger.info("Creating Anthropic model: %s", model_name)
        return AnthropicModel(
            model_name,
            provider=AnthropicProvider(api_key=api_key),
        )

    # Google AI Studio: use OpenAI-compatible endpoint
    if provider == "google":
        if not base_url or "generativelanguage.googleapis.com" in (base_url or ""):
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        logger.info("Creating Google model (OpenAI-compat): %s", model_name)

    # OpenAI-compatible (covers OpenAI, DeepSeek, Moonshot, Xiaomi, etc.)
    logger.info("Creating OpenAI-compatible model: %s%s", model_name, f" (base_url={base_url})" if base_url else "")
    provider_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        provider_kwargs["base_url"] = base_url
    return OpenAIModel(model_name, provider=OpenAIProvider(**provider_kwargs))
