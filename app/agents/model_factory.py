from functools import lru_cache

from pydantic_ai.models.openai import OpenAIModel, OpenAIModelName
from pydantic_ai.providers.azure import AzureProvider

from app import settings


@lru_cache
def _get_provider():
    return AzureProvider(
        azure_endpoint=settings.agent.deployment_endpoint.unicode_string(),
        api_version=settings.agent.api_version,
        api_key=settings.agent.token.get_secret_value(),
    )


def get_model(model_name: OpenAIModelName):
    """Get Open AI model."""
    return OpenAIModel(model_name, provider=_get_provider())
