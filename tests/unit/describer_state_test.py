"""Unit tests for describer_state repository."""

import json
from pathlib import Path

import pytest

from dope.repositories.describer_state import DescriberRepository


class TestDescriberRepository:
    """Tests for DescriberRepository class."""

    @pytest.fixture
    def repo(self, temp_dir):
        """Create a repository instance for testing."""
        return DescriberRepository(temp_dir / "describer-state.json")

    def test_get_file_state_returns_none_when_not_exists(self, repo):
        """Test get_file_state returns None for non-existent file."""
        result = repo.get_file_state("nonexistent.md")
        assert result is None

    def test_get_file_state_returns_state_when_exists(self, repo, temp_dir):
        """Test get_file_state returns state for existing file."""
        state_path = temp_dir / "describer-state.json"
        state_path.write_text(json.dumps({
            "readme.md": {"hash": "abc123", "summary": {"text": "summary"}}
        }))

        result = repo.get_file_state("readme.md")

        assert result["hash"] == "abc123"
        assert result["summary"]["text"] == "summary"


class TestIsFileChanged:
    """Tests for is_file_changed method."""

    @pytest.fixture
    def repo_with_state(self, temp_dir):
        """Repository with pre-existing state."""
        state_path = temp_dir / "describer-state.json"
        state_path.write_text(json.dumps({
            "readme.md": {"hash": "abc123", "summary": {"text": "summary"}}
        }))
        return DescriberRepository(state_path)

    def test_returns_true_for_new_file(self, repo_with_state):
        """Test returns True for file not in state."""
        result = repo_with_state.is_file_changed("new_file.md", "somehash")
        assert result is True

    def test_returns_true_for_changed_hash(self, repo_with_state):
        """Test returns True when hash has changed."""
        result = repo_with_state.is_file_changed("readme.md", "different_hash")
        assert result is True

    def test_returns_false_for_unchanged(self, repo_with_state):
        """Test returns False when hash matches."""
        result = repo_with_state.is_file_changed("readme.md", "abc123")
        assert result is False


class TestNeedsSummary:
    """Tests for needs_summary method."""

    @pytest.fixture
    def repo_with_state(self, temp_dir):
        """Repository with various file states."""
        state_path = temp_dir / "describer-state.json"
        state_path.write_text(json.dumps({
            "has_summary.md": {"hash": "abc", "summary": {"text": "summary"}},
            "no_summary.md": {"hash": "def", "summary": None},
            "skipped.md": {"hash": None, "skipped": True, "skip_reason": "test file"},
        }))
        return DescriberRepository(state_path)

    def test_returns_true_for_new_file(self, repo_with_state):
        """Test returns True for file not in state."""
        result = repo_with_state.needs_summary("new_file.md")
        assert result is True

    def test_returns_true_for_file_without_summary(self, repo_with_state):
        """Test returns True when summary is None."""
        result = repo_with_state.needs_summary("no_summary.md")
        assert result is True

    def test_returns_false_for_file_with_summary(self, repo_with_state):
        """Test returns False when summary exists."""
        result = repo_with_state.needs_summary("has_summary.md")
        assert result is False

    def test_returns_false_for_skipped_file(self, repo_with_state):
        """Test returns False for skipped files."""
        result = repo_with_state.needs_summary("skipped.md")
        assert result is False


class TestUpdateFileState:
    """Tests for update_file_state method."""

    def test_creates_new_file_state(self, temp_dir):
        """Test creating state for a new file."""
        repo = DescriberRepository(temp_dir / "state.json")

        repo.update_file_state(
            "new_file.md",
            file_hash="abc123",
            summary={"text": "summary"},
            priority="HIGH",
        )

        state = repo.load()
        assert state["new_file.md"]["hash"] == "abc123"
        assert state["new_file.md"]["summary"]["text"] == "summary"
        assert state["new_file.md"]["priority"] == "HIGH"

    def test_updates_existing_file_state(self, temp_dir):
        """Test updating state for existing file."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({
            "file.md": {"hash": "old", "summary": None}
        }))
        repo = DescriberRepository(state_path)

        repo.update_file_state(
            "file.md",
            file_hash="new_hash",
            summary={"text": "new summary"},
        )

        state = repo.load()
        assert state["file.md"]["hash"] == "new_hash"
        assert state["file.md"]["summary"]["text"] == "new summary"

    def test_marks_file_as_skipped(self, temp_dir):
        """Test marking a file as skipped."""
        repo = DescriberRepository(temp_dir / "state.json")

        repo.update_file_state(
            "test_file.py",
            skipped=True,
            skip_reason="Test file",
            metadata={"classification": "SKIP"},
        )

        state = repo.load()
        assert state["test_file.py"]["skipped"] is True
        assert state["test_file.py"]["skip_reason"] == "Test file"
        assert state["test_file.py"]["hash"] is None

    def test_preserves_unspecified_fields(self, temp_dir):
        """Test that unspecified fields are preserved."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({
            "file.md": {"hash": "abc", "summary": {"text": "summary"}, "priority": "HIGH"}
        }))
        repo = DescriberRepository(state_path)

        # Only update metadata
        repo.update_file_state("file.md", metadata={"new": "data"})

        state = repo.load()
        # Original fields should be preserved
        assert state["file.md"]["hash"] == "abc"
        assert state["file.md"]["summary"]["text"] == "summary"
        assert state["file.md"]["priority"] == "HIGH"
        assert state["file.md"]["metadata"]["new"] == "data"


class TestRemoveStaleFiles:
    """Tests for remove_stale_files method."""

    def test_removes_files_not_in_current(self, temp_dir):
        """Test that files not in current set are removed."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({
            "kept.md": {"hash": "abc"},
            "removed.md": {"hash": "def"},
        }))
        repo = DescriberRepository(state_path)

        removed = repo.remove_stale_files({"kept.md"})

        assert removed == ["removed.md"]
        state = repo.load()
        assert "kept.md" in state
        assert "removed.md" not in state

    def test_returns_empty_when_nothing_removed(self, temp_dir):
        """Test returns empty list when all files are current."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({
            "file1.md": {"hash": "abc"},
            "file2.md": {"hash": "def"},
        }))
        repo = DescriberRepository(state_path)

        removed = repo.remove_stale_files({"file1.md", "file2.md"})

        assert removed == []


class TestGetFilesNeedingSummary:
    """Tests for get_files_needing_summary method."""

    def test_returns_files_without_summary(self, temp_dir):
        """Test returns files that need summaries."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({
            "has_summary.md": {"hash": "abc", "summary": {"text": "summary"}},
            "needs_summary.md": {"hash": "def", "summary": None},
            "also_needs.md": {"hash": "ghi", "summary": None},
            "skipped.md": {"hash": None, "skipped": True},
        }))
        repo = DescriberRepository(state_path)

        result = repo.get_files_needing_summary()

        assert set(result) == {"needs_summary.md", "also_needs.md"}


class TestGetProcessableFiles:
    """Tests for get_processable_files method."""

    def test_returns_files_with_summaries(self, temp_dir):
        """Test returns only processable files."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({
            "ready.md": {"hash": "abc", "summary": {"text": "summary"}},
            "not_ready.md": {"hash": "def", "summary": None},
            "skipped.md": {"hash": None, "skipped": True},
        }))
        repo = DescriberRepository(state_path)

        result = repo.get_processable_files()

        assert "ready.md" in result
        assert "not_ready.md" not in result
        assert "skipped.md" not in result
