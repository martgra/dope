"""Unit tests for the versioned prompt registry."""

import pytest

from dope.prompts import Prompt, PromptRegistry


def test_registry_resolves_production_version():
    """PromptRegistry.get with no version falls back to the production manifest."""
    p = PromptRegistry.get("scope.align_doc")
    assert p.version == "v2-minimal"


def test_registry_resolves_explicit_version():
    """Callers can pin an explicit version to bypass the production manifest."""
    p = PromptRegistry.get("scope.align_doc", version="v1")
    assert p.version == "v1"
    assert "MINIMALITY" not in p.template


def test_registry_lists_versions_sorted():
    """list_versions returns all registered versions of a name, sorted."""
    versions = PromptRegistry.list_versions("scope.align_doc")
    assert versions == ["v1", "v2-minimal", "v3-diff"]


def test_registry_lists_names():
    """list_names includes every registered prompt across services."""
    names = PromptRegistry.list_names()
    assert "change.system" in names
    assert "judge.change_category" in names
    assert "suggest.system" in names


def test_registry_get_unknown_name_raises():
    """Unknown prompt names raise KeyError."""
    with pytest.raises(KeyError):
        PromptRegistry.get("does_not_exist")


def test_registry_get_unknown_version_raises():
    """Unknown versions raise KeyError."""
    with pytest.raises(KeyError):
        PromptRegistry.get("scope.align_doc", version="v99")


def test_prompt_render_substitutes_placeholders():
    """Prompt.render applies str.format with the given kwargs."""
    p = Prompt(name="t", version="v1", template="Hello, {name}!")
    assert p.render(name="World") == "Hello, World!"


def test_registered_prompt_has_description():
    """The tightened align_doc variant carries a description of why it exists."""
    p = PromptRegistry.get("scope.align_doc", version="v2-minimal")
    assert "MINIMALITY" in p.template
    assert p.description  # non-empty


def test_change_system_has_both_versions():
    """change.system has both v1 and v2-minimal for A/B."""
    versions = PromptRegistry.list_versions("change.system")
    assert "v1" in versions
    assert "v2-minimal" in versions
