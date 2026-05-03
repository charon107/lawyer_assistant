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
    openai_api_key: str | None = None,
    anthropic_api_key: str | None = None,
    base_url: str | None = None,
) -> OpenAIModel | AnthropicModel:
    """Create a PydanticAI model based on provider configuration.

    Args:
        provider: "openai" (OpenAI-compatible) or "anthropic". Defaults to settings.LLM_PROVIDER.
        model_name: Model name. Defaults to settings.AI_MODEL.
        openai_api_key: API key for OpenAI-compatible services. Defaults to settings.OPENAI_API_KEY.
        anthropic_api_key: API key for Anthropic. Defaults to settings.ANTHROPIC_API_KEY.
        base_url: Custom base URL for OpenAI-compatible APIs. Defaults to settings.LLM_BASE_URL.

    Returns:
        OpenAIModel or AnthropicModel instance.
    """
    provider = provider or settings.LLM_PROVIDER
    model_name = model_name or settings.AI_MODEL
    openai_api_key = openai_api_key or settings.OPENAI_API_KEY
    anthropic_api_key = anthropic_api_key or settings.ANTHROPIC_API_KEY
    base_url = base_url or settings.LLM_BASE_URL

    if provider == "anthropic":
        logger.info(f"Creating Anthropic model: {model_name}")
        return AnthropicModel(
            model_name,
            provider=AnthropicProvider(api_key=anthropic_api_key),
        )

    # OpenAI-compatible (covers OpenAI, DeepSeek, Groq, etc.)
    logger.info(f"Creating OpenAI-compatible model: {model_name}" + (f" (base_url={base_url})" if base_url else ""))
    provider_kwargs: dict[str, Any] = {"api_key": openai_api_key}
    if base_url:
        provider_kwargs["base_url"] = base_url
    return OpenAIModel(model_name, provider=OpenAIProvider(**provider_kwargs))
