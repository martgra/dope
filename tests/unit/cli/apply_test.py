"""Tests for shared documentation application helpers."""

from unittest.mock import Mock

import dope.cli.apply as apply_command


def test_apply_suggestions_materializes_and_writes_each_change(monkeypatch):
    """Each suggestion is materialized and written in order."""
    docs_changer = Mock()
    suggestions = ["first", "second"]
    docs_changer.apply_suggestion.side_effect = [
        ("docs/one.md", "one"),
        ("docs/two.md", "two"),
    ]
    write_change = Mock()

    monkeypatch.setattr(apply_command, "track", lambda changes, **_kwargs: changes)
    monkeypatch.setattr(apply_command, "_apply_change", write_change)

    applied_count = apply_command.apply_suggestions(docs_changer, suggestions)

    assert applied_count == 2
    assert docs_changer.apply_suggestion.call_args_list == [(("first",), {}), (("second",), {})]
    assert write_change.call_args_list == [
        (("docs/one.md", "one"), {}),
        (("docs/two.md", "two"), {}),
    ]
