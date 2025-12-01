"""Unit tests for config_io module - YAML config loading and generation."""

from pathlib import Path

import pytest
import yaml

from dope.core.config_io import (
    generate_local_cache,
    generate_local_config_file,
    load_settings_from_yaml,
)
from dope.models.settings import Settings


def test_load_settings_from_yaml(temp_file):
    """Test loading settings from a valid YAML file."""
    config_content = """
state_directory: /tmp/test
docs:
  doc_filetypes:
    - .md
    - .mdx
git:
  default_branch: develop
"""
    config_path = temp_file("config.yaml", config_content)

    result = load_settings_from_yaml(config_path)

    assert result["state_directory"] == "/tmp/test"
    assert result["git"]["default_branch"] == "develop"


def test_load_settings_from_yaml_empty_file(temp_file):
    """Test loading from empty YAML returns None (yaml.safe_load behavior)."""
    config_path = temp_file("empty.yaml", "")

    result = load_settings_from_yaml(config_path)

    assert result is None


def test_load_settings_from_yaml_invalid_syntax(temp_file):
    """Test that invalid YAML raises an exception."""
    config_path = temp_file("invalid.yaml", "key: [invalid yaml")

    with pytest.raises(yaml.YAMLError):
        load_settings_from_yaml(config_path)


def test_generate_local_config_file(temp_dir, monkeypatch):
    """Test generating a local config file."""
    monkeypatch.chdir(temp_dir)

    settings = Settings(state_directory=temp_dir / "state")

    generate_local_config_file("dope.yaml", settings)

    config_path = temp_dir / "dope.yaml"
    assert config_path.exists()

    # Verify content is valid YAML
    with config_path.open() as f:
        loaded = yaml.safe_load(f)

    assert "state_directory" in loaded


def test_generate_local_cache_creates_directory(temp_dir):
    """Test that generate_local_cache creates the cache directory."""
    cache_path = temp_dir / ".dope"

    result = generate_local_cache(cache_path)

    assert result == cache_path
    assert cache_path.is_dir()


def test_generate_local_cache_creates_gitignore(temp_dir):
    """Test that generate_local_cache creates .gitignore by default."""
    cache_path = temp_dir / ".dope"

    generate_local_cache(cache_path)

    gitignore = cache_path / ".gitignore"
    assert gitignore.exists()
    assert gitignore.read_text() == "*"


def test_generate_local_cache_no_gitignore_when_add_to_git(temp_dir):
    """Test that .gitignore is not created when add_to_git=True."""
    cache_path = temp_dir / ".dope"

    generate_local_cache(cache_path, add_to_git=True)

    gitignore = cache_path / ".gitignore"
    assert not gitignore.exists()


def test_generate_local_cache_idempotent(temp_dir):
    """Test that generate_local_cache can be called multiple times safely."""
    cache_path = temp_dir / ".dope"

    # First call
    generate_local_cache(cache_path)

    # Create a file in the cache
    (cache_path / "state.json").write_text("{}")

    # Second call should not fail or remove existing files
    generate_local_cache(cache_path)

    assert (cache_path / "state.json").exists()
