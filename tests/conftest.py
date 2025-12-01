"""Shared test fixtures for all test levels.

This module provides reusable fixtures that avoid duplication across
unit, integration, and e2e tests. Each fixture is documented with its
purpose and scope.
"""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from git import Repo

from dope.models.settings import CodeRepoSettings, DocSettings, Settings


# -----------------------------------------------------------------------------
# Temp Directory Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after test.

    Use this for tests needing file system operations without git.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir: Path):
    """Factory fixture to create temp files with content.

    Returns a function that creates files in the temp directory.
    """

    def _create_file(name: str, content: str = "") -> Path:
        file_path = temp_dir / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path

    return _create_file


# -----------------------------------------------------------------------------
# Git Repository Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def git_repo():
    """Create a minimal git repository for testing.

    Provides (repo_path, repo) tuple with initial commit on main branch.
    Use for tests that need git operations.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Repo.init(tmpdir)
        repo_path = Path(tmpdir)

        # Configure git user (required for commits)
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Create initial commit
        readme = repo_path / "README.md"
        readme.write_text("# Test Project\n")
        repo.index.add([str(readme)])
        repo.index.commit("Initial commit")

        # Ensure main branch exists
        repo.git.branch("-M", "main")

        yield repo_path, repo


@pytest.fixture
def git_repo_with_changes(git_repo):
    """Git repository with uncommitted changes for diff testing.

    Adds files and modifies them to create a diff scenario.
    """
    repo_path, repo = git_repo

    # Add and commit some files
    files = {
        "src/main.py": "def main():\n    pass\n",
        "src/utils.py": "def helper():\n    return True\n",
        "docs/guide.md": "# Guide\n\nSome documentation.\n",
    }

    for rel_path, content in files.items():
        file_path = repo_path / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        repo.index.add([str(rel_path)])

    repo.index.commit("Add source files")

    # Now modify files to create uncommitted changes
    (repo_path / "src/main.py").write_text("def main():\n    print('hello')\n")
    (repo_path / "src/new_feature.py").write_text("def feature():\n    pass\n")

    yield repo_path, repo


# -----------------------------------------------------------------------------
# Settings Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_settings(temp_dir: Path) -> Settings:
    """Create mock Settings with temp directory for state.

    Returns Settings with:
    - state_directory pointing to temp dir
    - No agent configured (agent=None)
    """
    return Settings(
        state_directory=temp_dir,
        docs=DocSettings(),
        git=CodeRepoSettings(),
        agent=None,
    )


@pytest.fixture
def mock_settings_with_state(mock_settings: Settings) -> Settings:
    """Settings with state directory created."""
    mock_settings.state_directory.mkdir(parents=True, exist_ok=True)
    return mock_settings


# -----------------------------------------------------------------------------
# State File Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def state_file(temp_dir: Path):
    """Factory to create state files with given content.

    Returns function to create JSON state files.
    """

    def _create_state(name: str, content: dict[str, Any]) -> Path:
        state_path = temp_dir / name
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(content))
        return state_path

    return _create_state


@pytest.fixture
def sample_doc_state() -> dict[str, Any]:
    """Sample documentation state for testing."""
    return {
        "docs/guide.md": {
            "hash": "abc123",
            "summary": {
                "description": "A guide to using the project",
                "key_topics": ["installation", "usage"],
            },
        },
        "docs/api.md": {
            "hash": "def456",
            "summary": None,
        },
    }


@pytest.fixture
def sample_code_state() -> dict[str, Any]:
    """Sample code state with metadata for testing."""
    return {
        "src/main.py": {
            "hash": "111222",
            "summary": {
                "description": "Main entry point",
                "changes": ["Added logging"],
            },
            "priority": "HIGH",
            "metadata": {
                "classification": "HIGH",
                "magnitude": 0.8,
                "lines_added": 25,
                "lines_deleted": 5,
            },
        },
        "src/utils.py": {
            "hash": "333444",
            "summary": {
                "description": "Utility functions",
                "changes": ["Minor refactor"],
            },
            "priority": "NORMAL",
            "metadata": {
                "classification": "NORMAL",
                "magnitude": 0.3,
            },
        },
        "tests/test_main.py": {
            "hash": None,
            "skipped": True,
            "skip_reason": "Trivial file type: test",
            "metadata": {"classification": "SKIP"},
        },
    }


# -----------------------------------------------------------------------------
# Mock Agent Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_agent():
    """Create a mock agent that returns predefined responses.

    Returns a MagicMock configured for agent.run_sync() calls.
    """
    agent = MagicMock()

    # Create mock output
    mock_output = MagicMock()
    mock_output.model_dump.return_value = {
        "description": "Test description",
        "changes": ["Test change"],
    }

    # Configure run_sync return value
    mock_result = MagicMock()
    mock_result.output = mock_output
    agent.run_sync.return_value = mock_result

    return agent


@pytest.fixture
def mock_async_agent():
    """Create a mock agent for async operations.

    Returns a MagicMock configured for agent.run() async calls.
    """
    import asyncio

    agent = MagicMock()

    # Create mock output
    mock_output = MagicMock()
    mock_output.model_dump.return_value = {
        "description": "Test description",
        "changes": ["Test change"],
    }

    # Configure async run return value
    mock_result = MagicMock()
    mock_result.output = mock_output

    # Create a coroutine that returns the mock result
    async def async_run(*args, **kwargs):
        await asyncio.sleep(0)  # Yield to event loop
        return mock_result

    agent.run = async_run

    return agent


@pytest.fixture
def mock_suggester_agent():
    """Create a mock agent for suggestion generation."""
    from dope.models.domain.documentation import (
        ChangeSuggestion,
        DocSuggestions,
        SuggestedChange,
    )
    from dope.models.enums import ChangeType

    agent = MagicMock()

    # Create proper suggestion output
    mock_output = DocSuggestions(
        changes_to_apply=[
            SuggestedChange(
                change_type=ChangeType.CHANGE,
                documentation_file_path="docs/guide.md",
                suggested_changes=[
                    ChangeSuggestion(
                        suggestion="Update installation steps",
                        code_references=["main.py"],
                    )
                ],
            )
        ]
    )

    mock_result = MagicMock()
    mock_result.output = mock_output
    agent.run_sync.return_value = mock_result

    return agent


# -----------------------------------------------------------------------------
# Consumer Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_file_consumer():
    """Mock FileConsumer for testing services without file system."""
    consumer = MagicMock()
    consumer.root_path = Path("/mock/path")
    consumer.discover_files.return_value = [
        Path("file1.md"),
        Path("file2.md"),
    ]
    consumer.get_content.return_value = b"Mock file content"
    return consumer


@pytest.fixture
def mock_git_consumer():
    """Mock GitConsumer for testing code services."""
    from dope.core.classification import ChangeMagnitude, FileClassification

    consumer = MagicMock()
    consumer.root_path = Path("/mock/repo")
    consumer.base_branch = "main"
    consumer.discover_files.return_value = [
        Path("src/main.py"),
        Path("src/utils.py"),
    ]
    consumer.get_content.return_value = b"+ added line\n- removed line\n"
    consumer.get_normalized_diff.return_value = b"+ added line\n"

    # Configure classification method
    def mock_classify(path: Path) -> FileClassification:
        if "test" in str(path).lower():
            return FileClassification(
                classification="SKIP", reason="Test file", matched_pattern="test_*.py"
            )
        elif path.name == "__init__.py":
            return FileClassification(
                classification="HIGH", reason="Entry point", matched_pattern="__init__.py"
            )
        return FileClassification(classification="NORMAL", reason="Regular file")

    consumer.classify_file_by_path.side_effect = mock_classify

    # Configure magnitude method
    def mock_magnitude(path: Path) -> ChangeMagnitude:
        return ChangeMagnitude(
            lines_added=10,
            lines_deleted=5,
            total_lines=15,
            is_rename=False,
            score=0.5,
        )

    consumer.get_change_magnitude.side_effect = mock_magnitude

    return consumer


# -----------------------------------------------------------------------------
# Usage Tracker Fixture
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_usage_tracker():
    """Mock usage tracker for testing without actual tracking."""
    tracker = MagicMock()
    tracker.usage = MagicMock()
    tracker.log = MagicMock()
    return tracker


# -----------------------------------------------------------------------------
# Cleanup Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear settings cache before each test to ensure isolation."""
    from dope.models.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
