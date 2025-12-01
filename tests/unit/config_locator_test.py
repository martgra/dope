"""Unit tests for config_locator module - finding config files."""

from pathlib import Path

import pytest

from dope.core.config_locator import find_project_root, locate_local_config_file


def test_find_project_root_in_git_repo(git_repo):
    """Test finding project root in a git repository."""
    repo_path, _ = git_repo

    # Create subdirectory
    subdir = repo_path / "src" / "nested"
    subdir.mkdir(parents=True)

    result = find_project_root(subdir)

    assert result == repo_path


def test_find_project_root_not_in_git_repo(temp_dir):
    """Test finding project root outside git returns the start path."""
    result = find_project_root(temp_dir)

    assert result == temp_dir


def test_locate_local_config_file_found(git_repo, monkeypatch):
    """Test locating config file when it exists."""
    repo_path, _ = git_repo

    # Create config file
    config_path = repo_path / "dope.yaml"
    config_path.write_text("key: value")

    # Change to repo directory
    monkeypatch.chdir(repo_path)

    result = locate_local_config_file("dope.yaml")

    assert result == config_path


def test_locate_local_config_file_in_parent(git_repo, monkeypatch):
    """Test finding config file in parent directory."""
    repo_path, _ = git_repo

    # Create config in root
    config_path = repo_path / "dope.yaml"
    config_path.write_text("key: value")

    # Create and change to subdirectory
    subdir = repo_path / "src" / "nested"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)

    result = locate_local_config_file("dope.yaml")

    assert result == config_path


def test_locate_local_config_file_not_found(git_repo, monkeypatch):
    """Test when config file doesn't exist."""
    repo_path, _ = git_repo
    monkeypatch.chdir(repo_path)

    result = locate_local_config_file("nonexistent.yaml")

    assert result is None


def test_locate_local_config_file_stops_at_project_root(git_repo, monkeypatch):
    """Test that search doesn't go beyond project root."""
    repo_path, _ = git_repo

    # Create subdirectory but put config outside repo (won't be found)
    subdir = repo_path / "src"
    subdir.mkdir()
    monkeypatch.chdir(subdir)

    # Config doesn't exist in repo
    result = locate_local_config_file("dope.yaml")

    assert result is None
