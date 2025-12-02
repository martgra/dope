"""Integration tests for DocChangeSuggester service.

These tests verify the suggester workflow with mocked agents.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dope.models.domain.documentation import (
    ChangeSuggestion,
    DocSuggestions,
    SuggestedChange,
)
from dope.models.enums import ChangeType
from dope.repositories.suggestion_state import SuggestionRepository
from dope.services.suggester.suggester_service import DocChangeSuggester


class TestDocChangeSuggesterWorkflow:
    """Integration tests for DocChangeSuggester."""

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a SuggestionRepository instance."""
        return SuggestionRepository(temp_dir / "suggestions.json")

    @pytest.fixture
    def suggester(self, repository, mock_suggester_agent, mock_usage_tracker):
        """Create a DocChangeSuggester with mocked agent."""
        return DocChangeSuggester(
            repository=repository,
            agent=mock_suggester_agent,
            usage_tracker=mock_usage_tracker,
        )

    def test_get_suggestions_with_valid_input(
        self, suggester, sample_doc_state, sample_code_state
    ):
        """Test get_suggestions generates suggestions from valid input."""
        result = suggester.get_suggestions(
            docs_change=sample_doc_state,
            code_change=sample_code_state,
        )

        assert isinstance(result, DocSuggestions)
        assert len(result.changes_to_apply) > 0

    def test_get_suggestions_filters_skipped_files(
        self, suggester, mock_suggester_agent
    ):
        """Test get_suggestions filters out skipped files."""
        code_state = {
            "src/main.py": {
                "hash": "abc",
                "summary": {"text": "Main module"},
                "priority": "HIGH",
            },
            "test_main.py": {
                "hash": None,
                "skipped": True,
                "skip_reason": "Test file",
            },
        }

        suggester.get_suggestions(
            docs_change={},
            code_change=code_state,
        )

        # Verify agent was called
        mock_suggester_agent.run_sync.assert_called_once()
        call_args = mock_suggester_agent.run_sync.call_args
        prompt = call_args.kwargs["user_prompt"]

        # Skipped file should not be in prompt
        assert "test_main.py" not in prompt
        assert "main.py" in prompt

    def test_get_suggestions_caches_results(
        self, repository, mock_suggester_agent, mock_usage_tracker
    ):
        """Test get_suggestions uses cached results when valid."""
        suggester = DocChangeSuggester(
            repository=repository,
            agent=mock_suggester_agent,
            usage_tracker=mock_usage_tracker,
        )

        code_state = {
            "src/main.py": {"hash": "abc", "summary": {"text": "Main"}, "priority": "NORMAL"},
        }
        doc_state = {}

        # First call - should invoke agent
        suggester.get_suggestions(docs_change=doc_state, code_change=code_state)
        assert mock_suggester_agent.run_sync.call_count == 1

        # Second call with same input - should use cache
        suggester.get_suggestions(docs_change=doc_state, code_change=code_state)
        # Agent should not be called again
        assert mock_suggester_agent.run_sync.call_count == 1

    def test_get_suggestions_regenerates_on_change(
        self, repository, mock_suggester_agent, mock_usage_tracker
    ):
        """Test get_suggestions regenerates when input changes."""
        suggester = DocChangeSuggester(
            repository=repository,
            agent=mock_suggester_agent,
            usage_tracker=mock_usage_tracker,
        )

        # First call
        suggester.get_suggestions(
            docs_change={},
            code_change={"src/main.py": {"hash": "abc", "summary": {"text": "v1"}}},
        )
        assert mock_suggester_agent.run_sync.call_count == 1

        # Second call with different input
        suggester.get_suggestions(
            docs_change={},
            code_change={"src/main.py": {"hash": "def", "summary": {"text": "v2"}}},
        )
        # Agent should be called again
        assert mock_suggester_agent.run_sync.call_count == 2

    def test_get_suggestions_returns_empty_when_no_code_changes(self, suggester):
        """Test get_suggestions returns empty when all code is skipped."""
        code_state = {
            "test_main.py": {"hash": None, "skipped": True, "skip_reason": "Test"},
        }

        result = suggester.get_suggestions(
            docs_change={},
            code_change=code_state,
        )

        assert isinstance(result, DocSuggestions)
        assert len(result.changes_to_apply) == 0

    def test_get_state_returns_current_suggestions(self, repository, temp_dir):
        """Test get_state returns current stored suggestions."""
        # Pre-populate state
        suggestions = DocSuggestions(
            changes_to_apply=[
                SuggestedChange(
                    change_type=ChangeType.CHANGE,
                    documentation_file_path="readme.md",
                    suggested_changes=[
                        ChangeSuggestion(suggestion="Update install", code_references=["main.py"])
                    ],
                )
            ]
        )
        repository.save_suggestions(suggestions, "somehash")

        suggester = DocChangeSuggester(repository=repository)
        result = suggester.get_state()

        assert len(result.changes_to_apply) == 1
        assert result.changes_to_apply[0].documentation_file_path == "readme.md"


class TestPromptBuilding:
    """Tests for prompt generation."""

    @pytest.fixture
    def suggester(self, temp_dir, mock_suggester_agent):
        """Create suggester for prompt testing."""
        repository = SuggestionRepository(temp_dir / "suggestions.json")
        return DocChangeSuggester(
            repository=repository,
            agent=mock_suggester_agent,
        )

    def test_prompt_includes_code_metadata(self, suggester, mock_suggester_agent):
        """Test that prompt includes code metadata for prioritization."""
        code_state = {
            "src/main.py": {
                "hash": "abc",
                "summary": {"description": "Main entry point"},
                "priority": "HIGH",
                "metadata": {
                    "classification": "HIGH",
                    "magnitude": 0.8,
                    "lines_added": 50,
                },
            },
        }

        suggester.get_suggestions(
            docs_change={},
            code_change=code_state,
        )

        call_args = mock_suggester_agent.run_sync.call_args
        prompt = call_args.kwargs["user_prompt"]

        # Should include priority/metadata info
        assert "HIGH" in prompt or "main.py" in prompt

    def test_prompt_orders_by_priority(self, suggester, mock_suggester_agent):
        """Test that HIGH priority files come before NORMAL."""
        code_state = {
            "normal.py": {
                "hash": "abc",
                "summary": {"description": "Normal file"},
                "priority": "NORMAL",
            },
            "critical.py": {
                "hash": "def",
                "summary": {"description": "Critical file"},
                "priority": "HIGH",
            },
        }

        suggester.get_suggestions(
            docs_change={},
            code_change=code_state,
        )

        call_args = mock_suggester_agent.run_sync.call_args
        prompt = call_args.kwargs["user_prompt"]

        # HIGH priority should appear before NORMAL
        high_pos = prompt.find("critical.py")
        normal_pos = prompt.find("normal.py")

        # Both should be in prompt
        assert high_pos != -1
        assert normal_pos != -1
        # HIGH should come first
        assert high_pos < normal_pos


class TestLazyAgentLoading:
    """Tests for lazy agent loading."""

    def test_provided_agent_used_directly(self, temp_dir, mock_suggester_agent):
        """Test that provided agent is used without lazy loading."""
        repository = SuggestionRepository(temp_dir / "suggestions.json")

        suggester = DocChangeSuggester(
            repository=repository,
            agent=mock_suggester_agent,
        )

        # Should return the provided agent directly
        assert suggester.agent is mock_suggester_agent
