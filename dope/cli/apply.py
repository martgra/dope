"""Apply suggested documentation changes."""

from pathlib import Path

import typer

from dope.cli.common import command_context, get_branch_option
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


@app.callback(invoke_without_command=True)
def apply(
    ctx: typer.Context,
    branch: get_branch_option() = None,
):
    """Apply previously generated documentation suggestions to files."""
    if ctx.resilient_parsing:
        return

    with command_context(branch=branch) as cmd_ctx:
        # Create services
        docs_changer = cmd_ctx.factory.docs_changer(Path("."), cmd_ctx.branch, cmd_ctx.tracker)
        suggester = cmd_ctx.factory.suggester()
        suggest_state = suggester.get_state()

        # Apply each suggested change
        for suggested_change in track(
            suggest_state.changes_to_apply, description="Applying documentation changes"
        ):
            path, content = docs_changer.apply_suggestion(suggested_change)
            _apply_change(path, content)
