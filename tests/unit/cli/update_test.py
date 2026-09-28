"""Tests for the all-in-one update command."""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import dope.cli.update as update_command


def _run_async_scanner(recorded_calls: list[tuple[object, object, str, int]]):
    """Build a scanner factory that records its command inputs."""

    def create_async_scanner(scanner, files, label, concurrency):
        recorded_calls.append((scanner, files, label, concurrency))

        async def run():
            return None

        return run

    return create_async_scanner


def test_update_dry_run_processes_scans_and_previews_suggestions(monkeypatch):
    """Dry-run scans both sources and previews without applying changes."""
    doc_scanner = Mock()
    doc_scanner.files_needing_summary.return_value = ["docs/guide.md"]
    doc_scanner.get_state.return_value = {"docs/guide.md": {}}
    code_scanner = Mock()
    code_scanner.files_needing_summary.return_value = ["src/main.py"]
    code_scanner.get_state.return_value = {"src/main.py": {}}
    suggester = Mock()
    suggestions = ["suggestion"]
    suggester.get_state.return_value = SimpleNamespace(changes_to_apply=suggestions)
    factory = Mock(
        doc_scanner=Mock(return_value=doc_scanner),
        code_scanner=Mock(return_value=code_scanner),
        suggester=Mock(return_value=suggester),
    )
    recorded_scans: list[tuple[object, object, str, int]] = []
    preview = Mock()
    context = SimpleNamespace(factory=factory, tracker=Mock(), branch="main")

    @contextmanager
    def command_context(branch=None):
        assert branch == "main"
        yield context

    monkeypatch.setattr(update_command, "command_context", command_context)
    monkeypatch.setattr(
        update_command.ProgressReporter,
        "create_async_scanner",
        _run_async_scanner(recorded_scans),
    )
    monkeypatch.setattr(update_command.StatusFormatter, "display_dry_run_preview", preview)
    monkeypatch.setattr(update_command, "_apply_change", Mock())
    cli_context = Mock(resilient_parsing=False)

    update_command.update(cli_context, dry_run=True, branch="main", concurrency=7)

    assert doc_scanner.scan.call_count == 1
    assert doc_scanner.build_term_index.call_count == 1
    assert code_scanner.scan.call_count == 1
    assert recorded_scans == [
        (doc_scanner, ["docs/guide.md"], "Scanning", 7),
        (code_scanner, ["src/main.py"], "Scanning", 7),
    ]
    suggester.get_suggestions.assert_called_once_with(
        docs_change={"docs/guide.md": {}}, code_change={"src/main.py": {}}
    )
    preview.assert_called_once_with(suggestions)
    factory.docs_changer.assert_not_called()


def test_update_applies_each_suggestion_when_not_dry_run(monkeypatch):
    """Non-dry-run applies suggestions sequentially after generating them."""
    doc_scanner = Mock()
    doc_scanner.files_needing_summary.return_value = []
    doc_scanner.get_state.return_value = {}
    code_scanner = Mock()
    code_scanner.files_needing_summary.return_value = []
    code_scanner.get_state.return_value = {}
    suggester = Mock()
    suggestions = ["first", "second"]
    suggester.get_state.return_value = SimpleNamespace(changes_to_apply=suggestions)
    docs_changer = Mock()
    docs_changer.apply_suggestion.side_effect = [
        ("docs/one.md", "one"),
        ("docs/two.md", "two"),
    ]
    factory = Mock(
        doc_scanner=Mock(return_value=doc_scanner),
        code_scanner=Mock(return_value=code_scanner),
        suggester=Mock(return_value=suggester),
        docs_changer=Mock(return_value=docs_changer),
    )
    context = SimpleNamespace(factory=factory, tracker=Mock(), branch="main")
    apply_change = Mock()

    @contextmanager
    def command_context(branch=None):
        assert branch is None
        yield context

    monkeypatch.setattr(update_command, "command_context", command_context)
    monkeypatch.setattr(update_command, "track", lambda changes, **_kwargs: changes)
    monkeypatch.setattr(update_command, "_apply_change", apply_change)
    cli_context = Mock(resilient_parsing=False)

    update_command.update(cli_context)

    assert docs_changer.apply_suggestion.call_args_list == [(("first",), {}), (("second",), {})]
    assert apply_change.call_args_list == [
        (("docs/one.md", "one"), {}),
        (("docs/two.md", "two"), {}),
    ]
