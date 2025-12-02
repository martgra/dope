"""Tests for DocChangeSuggester filtering and prioritization."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dope.models.domain.documentation import (
    ChangeSuggestion,
    DocSuggestions,
    SuggestedChange,
)
from dope.models.enums import ChangeType
from dope.repositories import SuggestionRepository
from dope.services.suggester.change_processor import ChangeProcessor
from dope.services.suggester.suggester_service import DocChangeSuggester


@pytest.fixture(name="suggester")
def suggester_fixture():
    """Create DocChangeSuggester with temp state file."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        f.write("{}")
        state_path = Path(f.name)

    repository = SuggestionRepository(state_path)
    suggester = DocChangeSuggester(repository=repository)
    yield suggester

    if state_path.exists():
        state_path.unlink()


class TestFilterProcessableFiles:
    """Test filtering of skipped and incomplete files."""

    def test_filter_removes_skipped_files(self):
        """Skipped files should be filtered out."""
        state = {
            "test_file.py": {"skipped": True, "skip_reason": "Test file"},
            "api.py": {"hash": "abc123", "summary": {"changes": ["something"]}},
        }

        result = ChangeProcessor.filter_processable_files(state)

        assert "test_file.py" not in result
        assert "api.py" in result

    def test_filter_removes_files_without_summary(self):
        """Files without summaries should be filtered out."""
        state = {
            "incomplete.py": {"hash": "abc123", "summary": None},
            "complete.py": {"hash": "def456", "summary": {"changes": ["something"]}},
        }

        result = ChangeProcessor.filter_processable_files(state)

        assert "incomplete.py" not in result
        assert "complete.py" in result

    def test_filter_keeps_valid_files(self):
        """Files with summaries should be kept."""
        state = {
            "api.py": {
                "hash": "abc123",
                "summary": {"changes": ["added function"]},
                "priority": "HIGH",
            },
            "utils.py": {"hash": "def456", "summary": {"changes": ["refactored"]}},
        }

        result = ChangeProcessor.filter_processable_files(state)

        assert len(result) == 2
        assert "api.py" in result
        assert "utils.py" in result


class TestSortByPriority:
    """Test priority-based sorting."""

    def test_high_priority_comes_first(self):
        """HIGH priority files should come before NORMAL."""
        state = {
            "normal.py": {
                "summary": {"changes": []},
                "priority": "NORMAL",
                "metadata": {"magnitude": 0.5},
            },
            "high.py": {
                "summary": {"changes": []},
                "priority": "HIGH",
                "metadata": {"magnitude": 0.3},
            },
        }

        result = ChangeProcessor.sort_by_priority(state)

        assert result[0][0] == "high.py"
        assert result[1][0] == "normal.py"

    def test_sorts_by_magnitude_within_priority(self):
        """Within same priority, higher magnitude should come first."""
        state = {
            "low_magnitude.py": {
                "summary": {"changes": []},
                "priority": "NORMAL",
                "metadata": {"magnitude": 0.3},
            },
            "high_magnitude.py": {
                "summary": {"changes": []},
                "priority": "NORMAL",
                "metadata": {"magnitude": 0.8},
            },
        }

        result = ChangeProcessor.sort_by_priority(state)

        assert result[0][0] == "high_magnitude.py"
        assert result[1][0] == "low_magnitude.py"

    def test_handles_missing_metadata(self):
        """Should handle files without metadata gracefully."""
        state = {
            "no_metadata.py": {"summary": {"changes": []}, "priority": "NORMAL"},
            "with_metadata.py": {
                "summary": {"changes": []},
                "priority": "HIGH",
                "metadata": {"magnitude": 0.5},
            },
        }

        result = ChangeProcessor.sort_by_priority(state)

        # Should still sort HIGH first
        assert result[0][0] == "with_metadata.py"


class TestPromptFormatter:
    """Test enhanced prompt formatting with metadata."""

    def test_formats_with_metadata(self):
        """Prompt should include metadata when requested."""
        state = {
            "api.py": {
                "hash": "abc123",
                "summary": {"changes": ["added function"]},
                "priority": "HIGH",
                "metadata": {"magnitude": 0.8, "lines_added": 50, "lines_deleted": 10},
            }
        }

        result = ChangeProcessor.format_changes_for_prompt(state, include_metadata=True)

        assert "api.py" in result
        assert "Priority: HIGH" in result
        assert "Change Magnitude: 0.80" in result
        assert "major" in result  # magnitude > 0.7
        assert "Lines Changed: +50 -10" in result

    def test_formats_without_metadata(self):
        """Prompt should exclude metadata when not requested."""
        state = {
            "api.py": {
                "hash": "abc123",
                "summary": {"changes": ["added function"]},
                "priority": "HIGH",
                "metadata": {"magnitude": 0.8},
            }
        }

        result = ChangeProcessor.format_changes_for_prompt(state, include_metadata=False)

        assert "api.py" in result
        assert "Priority" not in result
        assert "magnitude" not in result.lower()

    def test_filters_skipped_in_format(self):
        """Formatter should not include skipped files."""
        state = {
            "skipped.py": {"skipped": True, "skip_reason": "Test file"},
            "valid.py": {"hash": "abc123", "summary": {"changes": ["something"]}},
        }

        result = ChangeProcessor.format_changes_for_prompt(state, include_metadata=True)

        assert "skipped.py" not in result
        assert "valid.py" in result

    def test_orders_by_priority(self):
        """Formatted prompt should have HIGH priority files first."""
        state = {
            "normal.py": {
                "hash": "abc",
                "summary": {"changes": []},
                "priority": "NORMAL",
                "metadata": {"magnitude": 0.5},
            },
            "high.py": {
                "hash": "def",
                "summary": {"changes": []},
                "priority": "HIGH",
                "metadata": {"magnitude": 0.3},
            },
        }

        result = ChangeProcessor.format_changes_for_prompt(state, include_metadata=True)

        # Find positions in the formatted string
        high_pos = result.find("high.py")
        normal_pos = result.find("normal.py")

        assert high_pos < normal_pos, "HIGH priority should come before NORMAL"


class TestGetSuggestions:
    """Test the main get_suggestions method with filtering."""

    def test_filters_skipped_files_from_suggestions(self, suggester):
        """Skipped files should not be sent to LLM."""
        code_change = {
            "test_file.py": {"skipped": True, "skip_reason": "Test file"},
            "api.py": {
                "hash": "abc123",
                "summary": {"changes": ["added function"]},
                "priority": "HIGH",
            },
        }
        docs_change = {}

        with patch.object(suggester.agent, "run_sync") as mock_run:
            mock_result = MagicMock()
            mock_result.output = DocSuggestions(changes_to_apply=[])
            mock_run.return_value = mock_result

            suggester.get_suggestions(
                docs_change=docs_change, code_change=code_change
            )

            # Check that prompt doesn't include skipped file
            call_args = mock_run.call_args
            prompt = call_args.kwargs["user_prompt"]

            assert "test_file.py" not in prompt
            assert "api.py" in prompt

    def test_returns_empty_when_all_skipped(self, suggester):
        """Should return empty suggestions when all files are skipped."""
        code_change = {
            "test1.py": {"skipped": True, "skip_reason": "Test file"},
            "test2.py": {"skipped": True, "skip_reason": "Lock file"},
        }
        docs_change = {}

        result = suggester.get_suggestions(
            docs_change=docs_change, code_change=code_change
        )

        assert isinstance(result, DocSuggestions)
        assert len(result.changes_to_apply) == 0

    def test_includes_metadata_in_code_changes(self, suggester):
        """Code changes should include metadata in prompt."""
        code_change = {
            "api.py": {
                "hash": "abc123",
                "summary": {"changes": ["added function"]},
                "priority": "HIGH",
                "metadata": {"magnitude": 0.8, "lines_added": 50, "lines_deleted": 10},
            }
        }
        docs_change = {}

        with patch.object(suggester.agent, "run_sync") as mock_run:
            mock_result = MagicMock()
            mock_result.output = DocSuggestions(changes_to_apply=[])
            mock_run.return_value = mock_result

            suggester.get_suggestions(
                docs_change=docs_change, code_change=code_change
            )

            call_args = mock_run.call_args
            prompt = call_args.kwargs["user_prompt"]

            assert "Priority: HIGH" in prompt
            assert "Change Magnitude: 0.80" in prompt

    def test_docs_dont_include_metadata(self, suggester):
        """Documentation changes should not include metadata."""
        code_change = {}
        docs_change = {
            "README.md": {
                "hash": "abc123",
                "summary": {"content": "existing content"},
                "priority": "HIGH",
            }
        }

        with patch.object(suggester.agent, "run_sync") as mock_run:
            mock_result = MagicMock()
            mock_result.output = DocSuggestions(changes_to_apply=[])
            mock_run.return_value = mock_result

            # Need at least one code change to proceed
            suggester.get_suggestions(
                docs_change=docs_change,
                code_change={
                    "api.py": {"hash": "def", "summary": {"changes": ["something"]}}
                },
            )

            call_args = mock_run.call_args
            prompt = call_args.kwargs["user_prompt"]

            # Check docs section doesn't have metadata
            docs_section = prompt.split("<current_documentation>")[1].split(
                "</current_documentation>"
            )[0]
            assert "Priority" not in docs_section
            assert "magnitude" not in docs_section.lower()


class TestIntegration:
    """Integration tests for the full suggestion flow."""

    def test_full_workflow_with_filtering_and_priority(self, suggester):
        """Test complete workflow with mixed priority files."""
        code_change = {
            "test_file.py": {"skipped": True, "skip_reason": "Test file"},
            "utils.py": {
                "hash": "abc",
                "summary": {"changes": ["minor refactor"]},
                "priority": "NORMAL",
                "metadata": {"magnitude": 0.3, "lines_added": 10, "lines_deleted": 5},
            },
            "README.md": {
                "hash": "def",
                "summary": {"changes": ["major update"]},
                "priority": "HIGH",
                "metadata": {"magnitude": 0.9, "lines_added": 100, "lines_deleted": 20},
            },
        }
        docs_change = {
            "docs/api.md": {"hash": "ghi", "summary": {"content": "API docs"}}
        }

        with patch.object(suggester.agent, "run_sync") as mock_run:
            mock_result = MagicMock()
            mock_result.output = DocSuggestions(
                changes_to_apply=[
                    SuggestedChange(
                        change_type=ChangeType.CHANGE,
                        documentation_file_path="docs/api.md",
                        suggested_changes=[
                            ChangeSuggestion(
                                suggestion="Update API docs", code_references=["README.md"]
                            )
                        ],
                    )
                ]
            )
            mock_run.return_value = mock_result

            result = suggester.get_suggestions(
                docs_change=docs_change, code_change=code_change
            )

            # Verify LLM was called
            assert mock_run.called

            # Check prompt structure
            call_args = mock_run.call_args
            prompt = call_args.kwargs["user_prompt"]

            # Verify filtering
            assert "test_file.py" not in prompt

            # Verify priority ordering (README.md should come before utils.py)
            readme_pos = prompt.find("README.md")
            utils_pos = prompt.find("utils.py")
            assert readme_pos < utils_pos

            # Verify metadata included for code changes
            assert "Priority: HIGH" in prompt
            assert "major" in prompt  # magnitude > 0.7

            # Verify result
            assert isinstance(result, DocSuggestions)
