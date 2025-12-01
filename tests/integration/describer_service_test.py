"""Integration tests for DescriberService and CodeDescriberService.

These tests verify the service orchestration with mocked agents,
focusing on the workflow rather than individual components.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dope.core.classification import FileClassification, FileClassifier
from dope.repositories.describer_state import DescriberRepository
from dope.services.describer.describer_base import CodeDescriberService, DescriberService


class TestDescriberServiceWorkflow:
    """Integration tests for DescriberService."""

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a DescriberRepository instance."""
        return DescriberRepository(temp_dir / "state.json")

    @pytest.fixture
    def service(self, repository, mock_file_consumer, mock_usage_tracker):
        """Create a DescriberService instance."""
        return DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
            usage_tracker=mock_usage_tracker,
        )

    def test_scan_creates_state_file(self, service, temp_dir):
        """Test that scan creates a state file."""
        service.scan()

        assert (temp_dir / "state.json").exists()

    def test_scan_returns_discovered_files(self, service):
        """Test scan returns state for discovered files."""
        result = service.scan()

        assert "file1.md" in result
        assert "file2.md" in result

    def test_scan_computes_hashes(self, service, mock_file_consumer):
        """Test scan computes content hashes."""
        result = service.scan()

        # Hashes should be consistent for same content
        assert result["file1.md"]["hash"] == result["file2.md"]["hash"]
        mock_file_consumer.get_content.assert_called()

    def test_scan_preserves_summaries_on_unchanged(self, service, repository):
        """Test scan preserves existing summaries for unchanged files."""
        # First scan
        initial = service.scan()

        # Simulate adding a summary via repository
        state = repository.load()
        state["file1.md"]["summary"] = {"text": "existing summary"}
        repository.save(state)

        # Second scan - hash unchanged
        result = service.scan()

        assert result["file1.md"]["summary"]["text"] == "existing summary"

    def test_save_state_creates_directories(self, temp_dir, mock_file_consumer):
        """Test repository creates parent directories."""
        nested_path = temp_dir / "nested" / "deep" / "state.json"
        repository = DescriberRepository(nested_path)
        service = DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
        )

        service.scan()

        assert nested_path.exists()

    def test_describe_skips_files_with_summary(self, service, mock_agent):
        """Test describe skips files that already have summaries."""
        state_item = {
            "hash": "abc123",
            "summary": {"text": "existing"},
        }

        result = service.describe("file.md", state_item)

        # Should return unchanged
        assert result["summary"]["text"] == "existing"

    def test_describe_skips_skipped_files(self, service):
        """Test describe skips files marked as skipped."""
        state_item = {
            "hash": None,
            "skipped": True,
            "skip_reason": "Test file",
        }

        result = service.describe("test_file.py", state_item)

        assert result["skipped"] is True
        assert result.get("summary") is None

    @patch("dope.services.describer.strategies.get_doc_summarization_agent")
    def test_describe_generates_summary(self, mock_get_agent, service, mock_agent):
        """Test describe generates summary for file without one."""
        mock_get_agent.return_value = mock_agent

        state_item = {"hash": "abc123", "summary": None}

        result = service.describe("file.md", state_item)

        mock_agent.run_sync.assert_called_once()
        assert result["summary"] is not None


class TestCodeDescriberServiceFiltering:
    """Integration tests for CodeDescriberService with filtering."""

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a DescriberRepository instance."""
        return DescriberRepository(temp_dir / "state.json")

    @pytest.fixture
    def mock_classifier(self):
        """Create a mock FileClassifier."""
        return MagicMock(spec=FileClassifier)

    @pytest.fixture
    def service(self, repository, mock_git_consumer, mock_usage_tracker, mock_classifier):
        """Create a CodeDescriberService instance."""
        return CodeDescriberService(
            consumer=mock_git_consumer,
            repository=repository,
            classifier=mock_classifier,
            usage_tracker=mock_usage_tracker,
            enable_filtering=True,
        )

    def test_should_process_skips_test_files(self, service, mock_classifier):
        """Test should_process_file skips test files."""
        mock_classifier.classify.return_value = FileClassification(
            classification="SKIP", reason="Test file", matched_pattern="test_*.py"
        )

        result = service.should_process_file(Path("test_example.py"))

        assert result["process"] is False
        assert "test" in result["reason"].lower()

    def test_should_process_prioritizes_critical_files(
        self, service, mock_classifier, mock_git_consumer
    ):
        """Test should_process_file marks critical files as HIGH priority."""
        mock_classifier.classify.return_value = FileClassification(
            classification="HIGH", reason="Entry point", matched_pattern="__init__.py"
        )
        # Mock git operations
        mock_git_consumer.repo.git.diff.return_value = "5\t0\t__init__.py"
        mock_git_consumer.get_normalized_diff.return_value = b"diff content"

        result = service.should_process_file(Path("__init__.py"))

        assert result["process"] is True
        assert result["priority"] == "HIGH"

    def test_should_process_skips_pure_renames(self, service, mock_classifier, mock_git_consumer):
        """Test should_process_file skips pure rename operations."""
        mock_classifier.classify.return_value = FileClassification(
            classification="NORMAL", reason="Regular file"
        )
        # Mock git operations for pure rename
        mock_git_consumer.repo.git.diff.side_effect = [
            "0\t0\trenamed_file.py",  # numstat
            "rename old_file.py => renamed_file.py (98%)",  # summary
        ]
        mock_git_consumer.get_normalized_diff.return_value = b""

        result = service.should_process_file(Path("renamed_file.py"))

        assert result["process"] is False

    def test_scan_records_skipped_files(self, service, mock_classifier, mock_git_consumer):
        """Test scan records skipped files in state."""
        mock_git_consumer.discover_files.return_value = [
            Path("src/main.py"),
            Path("test_main.py"),
        ]

        # First file normal, second file skipped
        def classify_side_effect(path):
            if "test" in str(path):
                return FileClassification(
                    classification="SKIP", reason="Test file", matched_pattern="test_*.py"
                )
            return FileClassification(classification="NORMAL", reason="Regular file")

        mock_classifier.classify.side_effect = classify_side_effect

        # Mock git operations for normal file
        mock_git_consumer.repo.git.diff.side_effect = [
            "50\t20\tsrc/main.py",  # numstat
            "",  # summary
        ]
        mock_git_consumer.get_normalized_diff.return_value = b"diff content"
        mock_git_consumer.get_content.return_value = b"content"

        result = service.scan()

        # Skipped file should be recorded
        assert result["test_main.py"]["skipped"] is True
        assert "test" in result["test_main.py"]["skip_reason"].lower()

    def test_filtering_disabled_processes_all(
        self, temp_dir, mock_git_consumer, mock_usage_tracker
    ):
        """Test that disabling filtering processes all files."""
        repository = DescriberRepository(temp_dir / "state.json")
        service = CodeDescriberService(
            consumer=mock_git_consumer,
            repository=repository,
            usage_tracker=mock_usage_tracker,
            enable_filtering=False,
        )

        result = service.should_process_file(Path("any_file.py"))

        assert result["process"] is True
        assert "disabled" in result["reason"].lower()


class TestStateManagement:
    """Tests for state file management."""

    def test_load_state_returns_empty_when_no_file(self, temp_dir, mock_file_consumer):
        """Test get_state returns empty dict when file doesn't exist."""
        repository = DescriberRepository(temp_dir / "nonexistent.json")
        service = DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
        )

        result = service.get_state()

        assert result == {}

    def test_load_state_returns_saved_state(self, temp_dir, mock_file_consumer):
        """Test get_state returns previously saved state."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({"file.md": {"hash": "abc"}}))

        repository = DescriberRepository(state_path)
        service = DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
        )

        result = service.get_state()

        assert result["file.md"]["hash"] == "abc"

    def test_get_state_returns_current_state(self, temp_dir, mock_file_consumer):
        """Test get_state returns current state."""
        state_path = temp_dir / "state.json"
        state_path.write_text(json.dumps({"file.md": {"hash": "abc"}}))

        repository = DescriberRepository(state_path)
        service = DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
        )

        result = service.get_state()

        assert result["file.md"]["hash"] == "abc"


class TestFilesNeedingSummary:
    """Tests for files_needing_summary method."""

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a DescriberRepository instance."""
        return DescriberRepository(temp_dir / "state.json")

    @pytest.fixture
    def service(self, repository, mock_file_consumer, mock_usage_tracker):
        """Create a DescriberService instance."""
        return DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
            usage_tracker=mock_usage_tracker,
        )

    def test_returns_files_without_summary(self, service, repository):
        """Test returns files that need summaries."""
        # Set up state with mixed files
        state = {
            "needs_summary.md": {"hash": "abc", "summary": None},
            "has_summary.md": {"hash": "def", "summary": {"text": "existing"}},
            "skipped.md": {"hash": None, "skipped": True, "summary": None},
        }
        repository.save(state)

        result = service.files_needing_summary()

        assert "needs_summary.md" in result
        assert "has_summary.md" not in result
        assert "skipped.md" not in result

    def test_returns_empty_when_all_have_summaries(self, service, repository):
        """Test returns empty list when all files have summaries."""
        state = {
            "file1.md": {"hash": "abc", "summary": {"text": "summary1"}},
            "file2.md": {"hash": "def", "summary": {"text": "summary2"}},
        }
        repository.save(state)

        result = service.files_needing_summary()

        assert result == []


class TestDescribeAndSave:
    """Tests for describe_and_save method."""

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a DescriberRepository instance."""
        return DescriberRepository(temp_dir / "state.json")

    @pytest.fixture
    def service(self, repository, mock_file_consumer, mock_usage_tracker):
        """Create a DescriberService instance."""
        return DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
            usage_tracker=mock_usage_tracker,
        )

    @patch("dope.services.describer.strategies.get_doc_summarization_agent")
    def test_generates_and_persists_summary(self, mock_get_agent, service, repository, mock_agent):
        """Test describe_and_save generates summary and saves immediately."""
        mock_get_agent.return_value = mock_agent

        # Set up initial state
        state = {"file.md": {"hash": "abc", "summary": None}}
        repository.save(state)

        result = service.describe_and_save("file.md")

        # Should have generated summary
        assert result["summary"] is not None

        # Should have persisted
        saved_state = repository.load()
        assert saved_state["file.md"]["summary"] is not None

    def test_skips_file_with_existing_summary(self, service, repository):
        """Test describe_and_save skips file that already has summary."""
        state = {"file.md": {"hash": "abc", "summary": {"text": "existing"}}}
        repository.save(state)

        result = service.describe_and_save("file.md")

        assert result["summary"]["text"] == "existing"

    def test_skips_skipped_files(self, service, repository):
        """Test describe_and_save skips files marked as skipped."""
        state = {"file.md": {"hash": None, "skipped": True, "summary": None}}
        repository.save(state)

        result = service.describe_and_save("file.md")

        assert result["skipped"] is True
        assert result.get("summary") is None


class TestBuildTermIndex:
    """Tests for build_term_index method."""

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a DescriberRepository instance."""
        return DescriberRepository(temp_dir / "state.json")

    def test_builds_index_when_configured(self, temp_dir, mock_file_consumer, repository):
        """Test build_term_index builds index when path is configured."""
        index_path = temp_dir / "doc-terms.json"
        service = DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
            doc_term_index_path=index_path,
        )

        # Set up state with summaries
        state = {
            "docs/api.md": {
                "hash": "abc",
                "summary": {
                    "sections": [
                        {"section_name": "API", "references": ["endpoint", "REST"]}
                    ]
                },
            }
        }
        repository.save(state)

        result = service.build_term_index()

        assert result is True
        assert index_path.exists()

    def test_returns_false_when_no_path_configured(self, mock_file_consumer, repository):
        """Test build_term_index returns False when no path configured."""
        service = DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
            doc_term_index_path=None,
        )

        result = service.build_term_index()

        assert result is False

    def test_uses_cache_when_valid(self, temp_dir, mock_file_consumer, repository):
        """Test build_term_index uses cached index when valid."""
        index_path = temp_dir / "doc-terms.json"
        service = DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
            doc_term_index_path=index_path,
        )

        # Set up state
        state = {
            "docs/api.md": {
                "hash": "abc",
                "summary": {"sections": [{"section_name": "API", "references": []}]},
            }
        }
        repository.save(state)

        # First build - should rebuild
        first_result = service.build_term_index()
        assert first_result is True

        # Second build should use cache (returns False = no rebuild needed)
        result = service.build_term_index()
        assert result is False


class TestDescribeFilesParallel:
    """Tests for parallel file description."""

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a DescriberRepository instance."""
        return DescriberRepository(temp_dir / "state.json")

    @pytest.fixture
    def service(self, repository, mock_file_consumer, mock_usage_tracker):
        """Create a DescriberService instance."""
        return DescriberService(
            consumer=mock_file_consumer,
            repository=repository,
            usage_tracker=mock_usage_tracker,
        )

    @patch("dope.services.describer.strategies.get_doc_summarization_agent")
    def test_processes_multiple_files_in_parallel(
        self, mock_get_agent, service, repository, mock_async_agent
    ):
        """Test describe_files_parallel processes multiple files."""
        import asyncio

        mock_get_agent.return_value = mock_async_agent

        # Set up state with files needing summaries
        state = {
            "file1.md": {"hash": "abc", "summary": None},
            "file2.md": {"hash": "def", "summary": None},
            "file3.md": {"hash": "ghi", "summary": None},
        }
        repository.save(state)

        results = asyncio.run(
            service.describe_files_parallel(
                ["file1.md", "file2.md", "file3.md"],
                max_concurrency=2,
            )
        )

        # Check all files were processed
        assert len(results) == 3
        assert all(r.get("summary") is not None for r in results.values())

        # Check state was persisted
        saved_state = repository.load()
        assert saved_state["file1.md"]["summary"] is not None
        assert saved_state["file2.md"]["summary"] is not None
        assert saved_state["file3.md"]["summary"] is not None

    def test_skips_files_with_existing_summary(self, service, repository):
        """Test parallel describe skips files that already have summaries."""
        import asyncio

        state = {
            "has_summary.md": {"hash": "abc", "summary": {"text": "existing"}},
        }
        repository.save(state)

        results = asyncio.run(service.describe_files_parallel(["has_summary.md"]))

        # Should return existing summary without calling agent
        assert results["has_summary.md"]["summary"] == {"text": "existing"}

    def test_skips_skipped_files(self, service, repository):
        """Test parallel describe skips files marked as skipped."""
        import asyncio

        state = {
            "skipped.md": {"hash": None, "skipped": True, "summary": None},
        }
        repository.save(state)

        results = asyncio.run(service.describe_files_parallel(["skipped.md"]))

        assert results["skipped.md"].get("skipped") is True
        assert results["skipped.md"].get("summary") is None
