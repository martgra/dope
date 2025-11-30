"""Tests for CodeDescriberService filtering logic."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from dope.consumers.git_consumer import ChangeMagnitude, FileClassification, GitConsumer
from dope.services.describer.describer_base import CodeDescriberService


@pytest.fixture(name="mock_consumer")
def mock_consumer_fixture():
    """Create a mock GitConsumer."""
    consumer = Mock(spec=GitConsumer)
    consumer.root_path = Path("/mock/repo")
    return consumer


@pytest.fixture(name="service")
def service_fixture(mock_consumer):
    """Create CodeDescriberService with mocked consumer."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
        f.write('{}')  # Initialize with empty JSON
        state_path = Path(f.name)

    service = CodeDescriberService(
        consumer=mock_consumer, state_filepath=state_path, enable_filtering=True
    )
    yield service

    # Cleanup
    if state_path.exists():
        state_path.unlink()


@pytest.fixture(name="service_no_filter")
def service_no_filter_fixture(mock_consumer):
    """Create CodeDescriberService with filtering disabled."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
        f.write('{}')  # Initialize with empty JSON
        state_path = Path(f.name)

    service = CodeDescriberService(
        consumer=mock_consumer, state_filepath=state_path, enable_filtering=False
    )
    yield service

    if state_path.exists():
        state_path.unlink()


class TestShouldProcessFile:
    """Test the should_process_file decision logic."""

    def test_skip_trivial_file(self, service, mock_consumer):
        """Test files should be skipped."""
        file_path = Path("test_api.py")

        mock_consumer.classify_file_by_path.return_value = FileClassification(
            classification="SKIP", reason="Trivial file type: test", matched_pattern="test_*.py"
        )

        decision = service.should_process_file(file_path)

        assert decision["process"] is False
        assert "test" in decision["reason"].lower()
        assert decision["priority"] is None

    def test_process_high_priority_file(self, service, mock_consumer):
        """High priority files should always be processed."""
        file_path = Path("README.md")

        mock_consumer.classify_file_by_path.return_value = FileClassification(
            classification="HIGH", reason="Critical file type: readme"
        )

        mock_consumer.get_change_magnitude.return_value = ChangeMagnitude(
            lines_added=2,
            lines_deleted=1,
            total_lines=3,
            is_rename=False,
            score=0.2,  # Small change
        )

        mock_consumer.get_normalized_diff.return_value = b"some diff"

        decision = service.should_process_file(file_path)

        assert decision["process"] is True
        assert decision["priority"] == "HIGH"

    def test_skip_pure_rename(self, service, mock_consumer):
        """Pure renames should be skipped."""
        file_path = Path("new_name.py")

        mock_consumer.classify_file_by_path.return_value = FileClassification(
            classification="NORMAL", reason="Regular file"
        )

        mock_consumer.get_change_magnitude.return_value = ChangeMagnitude(
            lines_added=0,
            lines_deleted=0,
            total_lines=0,
            is_rename=True,
            score=0.1,  # Low score due to pure rename
            rename_similarity=98,
        )

        decision = service.should_process_file(file_path)

        assert decision["process"] is False
        assert "rename" in decision["reason"].lower()
        assert decision["metadata"]["rename_similarity"] == 98

    def test_skip_trivial_change(self, service, mock_consumer):
        """Small changes in normal files should be skipped."""
        file_path = Path("utils.py")

        mock_consumer.classify_file_by_path.return_value = FileClassification(
            classification="NORMAL", reason="Regular file"
        )

        mock_consumer.get_change_magnitude.return_value = ChangeMagnitude(
            lines_added=2,
            lines_deleted=1,
            total_lines=3,
            is_rename=False,
            score=0.15,  # Below threshold
        )

        decision = service.should_process_file(file_path)

        assert decision["process"] is False
        assert "trivial" in decision["reason"].lower()

    def test_skip_whitespace_only_changes(self, service, mock_consumer):
        """Formatting-only changes should be skipped."""
        file_path = Path("api.py")

        mock_consumer.classify_file_by_path.return_value = FileClassification(
            classification="NORMAL", reason="Regular file"
        )

        mock_consumer.get_change_magnitude.return_value = ChangeMagnitude(
            lines_added=10,
            lines_deleted=10,
            total_lines=20,
            is_rename=False,
            score=0.4,  # Significant score
        )

        # But normalized diff is empty (whitespace only)
        mock_consumer.get_normalized_diff.return_value = b""

        decision = service.should_process_file(file_path)

        assert decision["process"] is False
        assert "whitespace" in decision["reason"].lower() or "formatting" in decision[
            "reason"
        ].lower()

    def test_process_significant_change(self, service, mock_consumer):
        """Significant changes should be processed."""
        file_path = Path("core/engine.py")

        mock_consumer.classify_file_by_path.return_value = FileClassification(
            classification="NORMAL", reason="Regular file"
        )

        mock_consumer.get_change_magnitude.return_value = ChangeMagnitude(
            lines_added=50,
            lines_deleted=20,
            total_lines=70,
            is_rename=False,
            score=0.7,  # Significant
        )

        mock_consumer.get_normalized_diff.return_value = b"meaningful diff content"

        decision = service.should_process_file(file_path)

        assert decision["process"] is True
        assert decision["priority"] == "NORMAL"
        assert decision["metadata"]["magnitude"] == 0.7

    def test_filtering_disabled(self, service_no_filter):
        """When filtering is disabled, all files should be processed."""
        file_path = Path("test_file.py")

        decision = service_no_filter.should_process_file(file_path)

        assert decision["process"] is True
        assert "disabled" in decision["reason"].lower()


class TestScanFiles:
    """Test the _scan_files method with filtering."""

    def test_scan_with_filtering_enabled(self, service, mock_consumer):
        """Test that scan filters out trivial files."""
        mock_consumer.discover_files.return_value = [
            Path("test_api.py"),  # Should be skipped
            Path("api.py"),  # Should be processed
        ]

        # Mock classification
        def classify_side_effect(path):
            if "test_" in str(path):
                return FileClassification(
                    classification="SKIP", reason="Trivial file type: test"
                )
            return FileClassification(classification="NORMAL", reason="Regular file")

        mock_consumer.classify_file_by_path.side_effect = classify_side_effect

        # Mock magnitude for processed file
        mock_consumer.get_change_magnitude.return_value = ChangeMagnitude(
            lines_added=50,
            lines_deleted=20,
            total_lines=70,
            is_rename=False,
            score=0.7,
        )

        mock_consumer.get_normalized_diff.return_value = b"meaningful diff"
        mock_consumer.get_content.return_value = b"file content"
        mock_consumer.root_path = Path("/mock")

        result = service._scan_files()

        assert len(result) == 2
        assert result["test_api.py"]["skipped"] is True
        assert "test" in result["test_api.py"]["skip_reason"].lower()
        assert "hash" in result["api.py"]
        assert result["api.py"]["hash"] is not None

    def test_scan_with_filtering_disabled(self, service_no_filter, mock_consumer):
        """Test that scan processes all files when filtering is disabled."""
        mock_consumer.discover_files.return_value = [
            Path("test_api.py"),
            Path("api.py"),
        ]

        mock_consumer.get_content.return_value = b"file content"
        mock_consumer.root_path = Path("/mock")

        result = service_no_filter._scan_files()

        assert len(result) == 2
        # Both files should have hashes (not skipped)
        assert "hash" in result["test_api.py"]
        assert "hash" in result["api.py"]
        assert "skipped" not in result["test_api.py"]


class TestUpdateState:
    """Test state management with filtering."""

    def test_update_state_with_skipped_files(self, service):
        """Test that skipped files are properly recorded in state."""
        new_items = {
            "test_file.py": {
                "skipped": True,
                "skip_reason": "Trivial file type: test",
                "metadata": {"classification": "SKIP"},
            },
            "api.py": {
                "hash": "abc123",
                "priority": "NORMAL",
                "metadata": {"magnitude": 0.7},
            },
        }

        current_state = {}

        updated_state = service._update_state(new_items, current_state)

        assert updated_state["test_file.py"]["skipped"] is True
        assert updated_state["api.py"]["summary"] is None
        assert updated_state["api.py"]["hash"] == "abc123"

    def test_update_state_preserves_summaries(self, service):
        """Test that existing summaries are preserved when hash hasn't changed."""
        existing_summary = {"changes": ["something"]}

        current_state = {
            "api.py": {"hash": "abc123", "summary": existing_summary, "priority": "NORMAL"}
        }

        new_items = {"api.py": {"hash": "abc123", "priority": "NORMAL", "metadata": {}}}

        updated_state = service._update_state(new_items, current_state)

        assert updated_state["api.py"]["summary"] == existing_summary


class TestDescribe:
    """Test the describe method with filtering."""

    def test_describe_skips_filtered_files(self, service, mock_consumer):
        """Test that describe skips files marked as skipped."""
        state_item = {
            "skipped": True,
            "skip_reason": "Trivial file type: test",
            "metadata": {"classification": "SKIP"},
        }

        result = service.describe("test_file.py", state_item)

        assert result == state_item
        # Should not call get_content or LLM
        mock_consumer.get_content.assert_not_called()

    def test_describe_processes_normal_files(self, service, mock_consumer):
        """Test that describe processes files not marked as skipped."""
        state_item = {"hash": "abc123", "summary": None}

        mock_consumer.get_content.return_value = b"file content"
        mock_consumer.root_path = Path("/mock")

        # Mock the LLM call
        with patch.object(service, "_run_agent", return_value={"changes": ["something"]}):
            result = service.describe("api.py", state_item)

        assert result["summary"] == {"changes": ["something"]}
        mock_consumer.get_content.assert_called_once()


class TestIntegration:
    """Integration tests combining scan and describe."""

    def test_full_workflow_with_filtering(self, service, mock_consumer):
        """Test complete scan + describe workflow with filtering."""
        mock_consumer.discover_files.return_value = [
            Path("test_api.py"),
            Path("api.py"),
        ]

        def classify_side_effect(path):
            if "test_" in str(path):
                return FileClassification(
                    classification="SKIP", reason="Trivial file type: test"
                )
            return FileClassification(classification="NORMAL", reason="Regular file")

        mock_consumer.classify_file_by_path.side_effect = classify_side_effect
        mock_consumer.get_change_magnitude.return_value = ChangeMagnitude(
            lines_added=50,
            lines_deleted=20,
            total_lines=70,
            is_rename=False,
            score=0.7,
        )
        mock_consumer.get_normalized_diff.return_value = b"meaningful diff"
        mock_consumer.get_content.return_value = b"file content"
        mock_consumer.root_path = Path("/mock")

        # Scan
        state = service.scan()

        # Verify filtering worked
        assert state["test_api.py"]["skipped"] is True
        assert state["api.py"]["hash"] is not None

        # Describe
        with patch.object(service, "_run_agent", return_value={"changes": ["something"]}):
            for file_path, state_item in state.items():
                state[file_path] = service.describe(file_path, state_item)

        # Verify test file was skipped (no summary)
        assert state["test_api.py"]["skipped"] is True
        assert "summary" not in state["test_api.py"] or state["test_api.py"]["summary"] is None

        # Verify api.py was processed
        assert state["api.py"]["summary"] == {"changes": ["something"]}
