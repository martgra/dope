from functools import lru_cache
from typing import Literal

from pydantic_ai.models.openai import OpenAIModel, OpenAIModelName
from pydantic_ai.providers.azure import AzureProvider
from pydantic_ai.providers.openai import OpenAIProvider

from app import get_settings
from app.models.enums import Provider


@lru_cache
def _get_openai_provider(provider):
    settings = get_settings()
    if provider == Provider.AZURE:
        return AzureProvider(
            azure_endpoint=settings.agent.base_url.unicode_string(),
            api_version=settings.agent.api_version,
            api_key=settings.agent.token.get_secret_value(),
        )
    else:
        return OpenAIProvider(
            base_url=settings.agent.base_url.unicode_string() if settings.agent.base_url else None,
            api_key=settings.agent.token.get_secret_value(),
        )


def get_model(provider: Literal[Provider.OPENAI, Provider.AZURE], model_name: OpenAIModelName):
    """Get Open AI model."""
    if provider in (Provider.OPENAI, Provider.AZURE):
        return OpenAIModel(model_name, provider=_get_openai_provider(provider))
