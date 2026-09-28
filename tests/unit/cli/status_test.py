"""Tests for the status command."""

from unittest.mock import Mock

import dope.cli.status as status_command
from dope.models.domain.documentation import DocSuggestions, SuggestedChange
from dope.models.enums import ChangeType
from dope.repositories import JsonStateRepository, SuggestionRepository


def test_status_reads_suggestion_repository_schema(mock_settings_with_state, monkeypatch):
    """Status counts suggestions stored under the repository's suggestion key."""
    JsonStateRepository(mock_settings_with_state.doc_state_path).save(
        {"docs/guide.md": {"summary": {"sections": []}}}
    )
    JsonStateRepository(mock_settings_with_state.code_state_path).save(
        {"src/main.py": {"summary": {"description": "Updated"}}}
    )
    SuggestionRepository(mock_settings_with_state.suggestion_state_path).save_suggestions(
        DocSuggestions(
            changes_to_apply=[
                SuggestedChange(
                    change_type=ChangeType.ADD,
                    documentation_file_path="docs/new-guide.md",
                    suggested_changes=[],
                )
            ]
        ),
        state_hash="state-hash",
    )
    display_status = Mock()

    monkeypatch.setattr(status_command, "require_config", lambda: mock_settings_with_state)
    monkeypatch.setattr(status_command.StatusFormatter, "display_status", display_status)

    status_command.status()

    assert display_status.call_args.kwargs["docs_scanned"] == 1
    assert display_status.call_args.kwargs["code_scanned"] == 1
    assert display_status.call_args.kwargs["suggestions_count"] == 1
