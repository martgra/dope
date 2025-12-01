"""Tests for settings module and get_settings() caching behavior."""

from pathlib import Path

import pytest

from dope.models.settings import Settings, get_settings


def test_get_settings_returns_settings_instance():
    """Test that get_settings() returns a Settings instance."""
    settings = get_settings()
    assert isinstance(settings, Settings)


def test_get_settings_caches_result():
    """Test that get_settings() returns the same instance on repeated calls."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_get_settings_cache_can_be_cleared():
    """Test that cache can be cleared to reload settings."""
    settings1 = get_settings()
    get_settings.cache_clear()
    settings2 = get_settings()
    # After cache clear, should get a new instance
    assert settings1 is not settings2
    assert isinstance(settings2, Settings)


def test_settings_has_required_attributes():
    """Test that settings has expected attributes."""
    settings = get_settings()
    assert hasattr(settings, "state_directory")
    assert hasattr(settings, "docs")
    assert hasattr(settings, "git")
    assert hasattr(settings, "agent")


def test_settings_state_directory_is_path():
    """Test that state_directory is a Path object."""
    settings = get_settings()
    assert isinstance(settings.state_directory, Path)


def test_settings_docs_settings():
    """Test that docs settings are properly initialized."""
    settings = get_settings()
    assert hasattr(settings.docs, "doc_filetypes")
    assert hasattr(settings.docs, "exclude_dirs")
    assert hasattr(settings.docs, "docs_root")


def test_settings_git_settings():
    """Test that git settings are properly initialized."""
    settings = get_settings()
    assert hasattr(settings.git, "default_branch")
    assert hasattr(settings.git, "code_repo_root")


def test_settings_agent_can_be_none():
    """Test that agent settings can be None when not configured."""
    # This test may fail if there's a valid config file
    # Cache clear to ensure fresh load
    get_settings.cache_clear()
    settings = get_settings()
    # Agent might be None or configured depending on test environment
    assert settings.agent is None or hasattr(settings.agent, "provider")


def test_settings_immutability_not_enforced():
    """Test that settings can be modified (not frozen)."""
    settings = get_settings()
    # Should be able to modify settings
    original_branch = settings.git.default_branch
    settings.git.default_branch = "test-branch"
    assert settings.git.default_branch == "test-branch"
    # Restore original
    settings.git.default_branch = original_branch


def test_multiple_imports_same_cached_instance():
    """Test that multiple imports get the same cached instance."""
    from dope.models.settings import get_settings as get_settings_import1
    from dope.models.settings import get_settings as get_settings_import2

    settings1 = get_settings_import1()
    settings2 = get_settings_import2()
    assert settings1 is settings2
