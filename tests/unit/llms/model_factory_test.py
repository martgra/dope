"""Unit tests for dope.llms.model_factory TypeSafe helpers."""

from unittest.mock import patch

import pytest
from pydantic import SecretStr

from dope.exceptions import AgentNotConfiguredError
from dope.llms import model_factory
from dope.models.settings import Settings, TypeSafeSettings


@pytest.fixture(autouse=True)
def _clear_provider_cache():
    """Clear the TypeSafe provider cache before and after each test."""
    model_factory._get_typesafe_provider.cache_clear()
    yield
    model_factory._get_typesafe_provider.cache_clear()


def test_get_typesafe_model_raises_when_key_missing():
    """get_typesafe_model raises AgentNotConfiguredError when api_key is None."""
    with patch.object(model_factory, "get_settings", return_value=Settings(_env_file=None)):
        with pytest.raises(AgentNotConfiguredError, match="typesafe__API_KEY"):
            model_factory.get_typesafe_model()


def test_get_typesafe_model_builds_with_configured_key():
    """When api_key is set, get_typesafe_model returns a TypeSafeModel."""
    settings = Settings(typesafe=TypeSafeSettings(api_key=SecretStr("ts-test-key")))
    with patch.object(model_factory, "get_settings", return_value=settings):
        model = model_factory.get_typesafe_model()

    from pydantic_ai.models.typesafe import TypeSafeModel

    assert isinstance(model, TypeSafeModel)
