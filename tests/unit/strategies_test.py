"""Tests for describer strategy classes."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from dope.consumers.base import BaseConsumer
from dope.core.classification import FileClassification, FileClassifier
from dope.core.usage import UsageTracker
from dope.services.describer.strategies import (
    CodeAgentStrategy,
    CodeScanStrategy,
    DocAgentStrategy,
    DocScanStrategy,
)


class TestDocScanStrategy:
    """Tests for DocScanStrategy."""

    @pytest.fixture
    def mock_consumer(self):
        """Create a mock consumer."""
        consumer = Mock(spec=BaseConsumer)
        consumer.root_path = Path("/mock/docs")
        return consumer

    def test_scan_files_computes_hashes(self, mock_consumer):
        """Test scan_files returns hashes for all discovered files."""
        mock_consumer.discover_files.return_value = [
            Path("readme.md"),
            Path("api.md"),
        ]
        mock_consumer.get_content.side_effect = [b"readme content", b"api content"]

        strategy = DocScanStrategy()
        result = strategy.scan_files(mock_consumer)

        assert len(result) == 2
        assert "readme.md" in result
        assert "api.md" in result
        assert result["readme.md"]["hash"] is not None
        assert result["api.md"]["hash"] is not None

    def test_scan_files_returns_empty_for_no_files(self, mock_consumer):
        """Test scan_files returns empty dict when no files found."""
        mock_consumer.discover_files.return_value = []

        strategy = DocScanStrategy()
        result = strategy.scan_files(mock_consumer)

        assert result == {}


class TestCodeScanStrategy:
    """Tests for CodeScanStrategy."""

    @pytest.fixture
    def mock_git_consumer(self):
        """Create a mock GitConsumer."""
        from dope.consumers.git_consumer import GitConsumer

        consumer = Mock(spec=GitConsumer)
        consumer.root_path = Path("/mock/repo")
        consumer.repo = MagicMock()
        consumer.base_branch = "main"
        return consumer

    @pytest.fixture
    def mock_classifier(self):
        """Create a mock FileClassifier."""
        return Mock(spec=FileClassifier)

    @pytest.fixture
    def strategy(self, mock_git_consumer, mock_classifier):
        """Create a CodeScanStrategy instance."""
        return CodeScanStrategy(
            consumer=mock_git_consumer,
            classifier=mock_classifier,
            enable_filtering=True,
        )

    def test_should_process_skips_trivial_files(self, strategy, mock_classifier):
        """Test should_process_file skips test files."""
        mock_classifier.classify.return_value = FileClassification(
            classification="SKIP", reason="Test file", matched_pattern="test_*.py"
        )

        result = strategy.should_process_file(Path("test_api.py"))

        assert result["process"] is False
        assert "test" in result["reason"].lower()

    def test_should_process_when_filtering_disabled(self, mock_git_consumer, mock_classifier):
        """Test should_process_file returns True when filtering disabled."""
        strategy = CodeScanStrategy(
            consumer=mock_git_consumer,
            classifier=mock_classifier,
            enable_filtering=False,
        )

        result = strategy.should_process_file(Path("any_file.py"))

        assert result["process"] is True
        assert "disabled" in result["reason"].lower()

    def test_scan_files_with_filtering(
        self, strategy, mock_git_consumer, mock_classifier
    ):
        """Test scan_files filters out trivial files."""
        mock_git_consumer.discover_files.return_value = [
            Path("test_api.py"),
            Path("api.py"),
        ]

        def classify_side_effect(path):
            if "test_" in str(path):
                return FileClassification(
                    classification="SKIP", reason="Test file"
                )
            return FileClassification(classification="NORMAL", reason="Regular file")

        mock_classifier.classify.side_effect = classify_side_effect

        # Mock git operations for api.py
        mock_git_consumer.repo.git.diff.side_effect = [
            "50\t20\tapi.py",  # numstat
            "",  # summary
        ]
        mock_git_consumer.get_normalized_diff.return_value = b"meaningful diff"
        mock_git_consumer.get_content.return_value = b"file content"

        result = strategy.scan_files(mock_git_consumer)

        assert len(result) == 2
        assert result["test_api.py"]["skipped"] is True
        assert result["api.py"]["hash"] is not None
        assert "skipped" not in result["api.py"]

    def test_scan_files_without_filtering(self, mock_git_consumer, mock_classifier):
        """Test scan_files processes all files when filtering disabled."""
        strategy = CodeScanStrategy(
            consumer=mock_git_consumer,
            classifier=mock_classifier,
            enable_filtering=False,
        )

        mock_git_consumer.discover_files.return_value = [
            Path("test_api.py"),
            Path("api.py"),
        ]
        mock_git_consumer.get_content.return_value = b"file content"

        result = strategy.scan_files(mock_git_consumer)

        assert len(result) == 2
        assert "skipped" not in result["test_api.py"]
        assert "skipped" not in result["api.py"]


class TestDocAgentStrategy:
    """Tests for DocAgentStrategy."""

    @pytest.fixture
    def usage_tracker(self):
        """Create a UsageTracker instance."""
        return UsageTracker()

    @patch("dope.services.describer.strategies.get_doc_summarization_agent")
    def test_run_agent_calls_summarization_agent(self, mock_get_agent, usage_tracker):
        """Test run_agent calls the doc summarization agent."""
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value.output.model_dump.return_value = {
            "sections": [{"name": "Overview"}]
        }
        mock_get_agent.return_value = mock_agent

        strategy = DocAgentStrategy()
        result = strategy.run_agent(
            file_path="readme.md",
            content=b"# Readme\n\nContent here",
            usage_tracker=usage_tracker,
        )

        mock_agent.run_sync.assert_called_once()
        assert result == {"sections": [{"name": "Overview"}]}


class TestCodeAgentStrategy:
    """Tests for CodeAgentStrategy."""

    @pytest.fixture
    def mock_git_consumer(self):
        """Create a mock GitConsumer."""
        from dope.consumers.git_consumer import GitConsumer

        return Mock(spec=GitConsumer)

    @pytest.fixture
    def usage_tracker(self):
        """Create a UsageTracker instance."""
        return UsageTracker()

    @patch("dope.services.describer.strategies.get_code_change_agent")
    def test_run_agent_calls_code_change_agent(
        self, mock_get_agent, mock_git_consumer, usage_tracker
    ):
        """Test run_agent calls the code change agent with deps."""
        mock_agent = MagicMock()
        mock_agent.run_sync.return_value.output.model_dump.return_value = {
            "changes": ["Added function"]
        }
        mock_get_agent.return_value = mock_agent

        strategy = CodeAgentStrategy(consumer=mock_git_consumer)
        result = strategy.run_agent(
            file_path="api.py",
            content=b"def new_function(): pass",
            usage_tracker=usage_tracker,
        )

        mock_agent.run_sync.assert_called_once()
        # Verify deps were passed
        call_kwargs = mock_agent.run_sync.call_args.kwargs
        assert "deps" in call_kwargs
        assert call_kwargs["deps"].consumer == mock_git_consumer
        assert result == {"changes": ["Added function"]}
