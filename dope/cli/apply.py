"""Apply suggested documentation changes."""

from pathlib import Path
from typing import Annotated

import typer

from dope.cli.common import command_context, require_state_files
from dope.cli.ui import info, success, warning
from dope.core.progress import track

app = typer.Typer(
    epilog="""
Examples:
  # Apply suggestions using configured branch
  $ dope apply

  # Apply suggestions against specific branch
  $ dope apply --branch develop

  # Full workflow
  $ dope scan docs && dope scan code
  $ dope suggest
  $ dope apply
    """
)


def _apply_change(path: Path, content: str) -> None:
    """Write changes to file, creating directories if needed.

    Args:
        path: Path to the file to write
        content: Content to write to the file
    """
    path = Path(path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        file.write(content)


def apply_suggestions(docs_changer, suggestions: list) -> int:
    """Materialize and write each documentation suggestion.

    Args:
        docs_changer: Service that produces updated file content.
        suggestions: Documentation changes to apply.

    Returns:
        Number of suggestions applied.
    """
    for suggested_change in track(suggestions, description="Applying documentation changes"):
        path, content = docs_changer.apply_suggestion(suggested_change)
        _apply_change(path, content)
    return len(suggestions)


@app.callback(invoke_without_command=True)
def apply(
    ctx: typer.Context,
    branch: Annotated[
        str | None,
        typer.Option(
            "--branch",
            "-b",
            help="Branch to compare against (defaults to configured branch)",
        ),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Apply changes without asking for confirmation"),
    ] = False,
):
    """Apply previously generated documentation suggestions to files."""
    if ctx.resilient_parsing:
        return

    with command_context(branch=branch) as cmd_ctx:
        require_state_files(
            {"suggestions": cmd_ctx.settings.suggestion_state_path},
            "Run 'dope suggest' or 'dope update' first.",
        )

        # Create services
        docs_changer = cmd_ctx.factory.docs_changer(
            cmd_ctx.docs_root, cmd_ctx.code_root, cmd_ctx.branch, cmd_ctx.tracker
        )
        suggester = cmd_ctx.factory.suggester()
        suggest_state = suggester.get_state()
        suggestions = suggest_state.changes_to_apply

        if not suggestions:
            warning("There are no pending documentation suggestions to apply.")
            return

        if not yes and not typer.confirm(f"Apply {len(suggestions)} documentation suggestions?"):
            info("No files were changed.")
            return

        applied_count = apply_suggestions(docs_changer, suggestions)
        success(f"Applied {applied_count} documentation suggestions.")
