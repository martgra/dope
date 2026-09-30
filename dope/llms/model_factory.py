"""Factories for configured Pydantic AI models."""

from typing import Literal

from pydantic_ai.models.openai import (
    OpenAIChatModel,
    OpenAIChatModelSettings,
    OpenAIModelName,
)
from pydantic_ai.models.typesafe import TypeSafeModel, TypeSafeModelName
from pydantic_ai.providers.azure import AzureProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.typesafe import TypeSafeProvider

from dope.core.loop_cache import loop_scoped_cache
from dope.exceptions import AgentNotConfiguredError, ProviderError
from dope.llms.retry_config import get_retry_client
from dope.models.enums import Provider
from dope.models.settings import get_settings


@loop_scoped_cache
def _get_openai_provider(provider):
    settings = get_settings()
    if not settings.agent:
        raise AgentNotConfiguredError(
            "Agent settings not configured. Run 'dope config init' first."
        )
    http_client = get_retry_client()
    if provider == Provider.AZURE:
        if not settings.agent.base_url:
            raise ProviderError("azure", "base_url must be configured for Azure provider")
        return AzureProvider(
            azure_endpoint=settings.agent.base_url.unicode_string(),
            api_version=settings.agent.api_version,
            api_key=settings.agent.token.get_secret_value(),  # pylint: disable=no-member
            http_client=http_client,
        )
    else:
        return OpenAIProvider(
            base_url=settings.agent.base_url.unicode_string() if settings.agent.base_url else None,
            api_key=settings.agent.token.get_secret_value(),  # pylint: disable=no-member
            http_client=http_client,
        )


def get_model(provider: Literal[Provider.OPENAI, Provider.AZURE], model_name: OpenAIModelName):
    """Get an OpenAI-compatible chat model.

    Sets ``openai_reasoning_effort='none'`` because the GPT-5.6 family requires
    it when function tools (which pydantic-ai uses under the hood for
    structured ``output_type``) are combined with ``/v1/chat/completions``.
    The setting is a no-op on older models that ignore it.
    """
    if provider in (Provider.OPENAI, Provider.AZURE):
        return OpenAIChatModel(
            model_name,
            provider=_get_openai_provider(provider),
            settings=OpenAIChatModelSettings(openai_reasoning_effort="none"),
        )


@loop_scoped_cache
def _get_typesafe_provider() -> TypeSafeProvider:
    settings = get_settings()
    if settings.typesafe.api_key is None:
        raise AgentNotConfiguredError(
            "TypeSafe API key not configured. Set typesafe__API_KEY in .env."
        )
    return TypeSafeProvider(api_key=settings.typesafe.api_key.get_secret_value())  # pylint: disable=no-member


def get_typesafe_model(model_name: TypeSafeModelName = "jev-latest") -> TypeSafeModel:
    """Get a TypeSafe (Jev) System-One model.

    The API key is read from ``settings.typesafe.api_key``, populated from the
    ``typesafe__API_KEY`` env var (double-underscore delimiter). Use with an
    Agent whose output_type is bool (Noul), an Enum/Literal (Choice), or int
    with per-level instructions (Score) — the answer is a typed judgment, not
    free-form text.

    Args:
        model_name: TypeSafe model identifier. Defaults to "jev-latest".

    Returns:
        Configured TypeSafeModel ready to attach to a pydantic-ai Agent.

    Raises:
        AgentNotConfiguredError: When ``typesafe__API_KEY`` is not set.
    """
    return TypeSafeModel(model_name, provider=_get_typesafe_provider())
