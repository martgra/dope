"""Tests for shared CLI command helpers."""

from pathlib import Path
from unittest.mock import Mock

import pytest
import typer

from dope.cli.common import CommandContext, require_state_files
from dope.models.settings import CodeRepoSettings, DocSettings, Settings


def test_require_state_files_allows_existing_files(temp_dir: Path):
    """Existing prerequisite files allow command execution to continue."""
    state_path = temp_dir / "code-state.json"
    state_path.write_text("{}")

    require_state_files({"code scan state": state_path}, "Run the scan command first.")


def test_require_state_files_exits_with_missing_file_guidance(temp_dir: Path, capsys):
    """Missing prerequisite files stop the command with an actionable next step."""
    state_path = temp_dir / "code-state.json"

    with pytest.raises(typer.Exit, match="1"):
        require_state_files({"code scan state": state_path}, "Run 'dope scan code'.")

    output = capsys.readouterr().out
    assert "missing code scan state" in output
    assert "Run 'dope scan code'" in output


def test_command_context_uses_configured_roots(temp_dir: Path):
    """Configured documentation and code roots are available to every command."""
    docs_root = temp_dir / "docs"
    code_root = temp_dir / "code"
    settings = Settings(
        docs=DocSettings(docs_root=docs_root),
        git=CodeRepoSettings(code_repo_root=code_root),
    )

    context = CommandContext(settings, Mock())

    assert context.docs_root == docs_root
    assert context.code_root == code_root


def test_command_context_falls_back_to_current_directory():
    """Commands retain the current-directory fallback when roots are unset."""
    context = CommandContext(Settings(), Mock())

    assert context.docs_root == Path(".")
    assert context.code_root == Path(".")
