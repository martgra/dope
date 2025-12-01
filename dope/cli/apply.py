"""Apply suggested documentation changes."""

from pathlib import Path

import typer

from dope.cli.common import get_branch_option, resolve_branch
from dope.cli.factories import create_docs_changer, create_suggester
from dope.core.progress import track
from dope.core.usage import UsageTracker
from dope.core.utils import require_config

app = typer.Typer()


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

    settings = require_config()
    branch = resolve_branch(branch, settings)
    tracker = UsageTracker()

    # Create services using factories
    docs_changer = create_docs_changer(Path("."), branch, settings, tracker)
    suggester = create_suggester(settings)
    suggest_state = suggester.get_state()

    # Apply each suggested change
    for suggested_change in track(
        suggest_state.changes_to_apply, description="Applying documentation changes"
    ):
        path, content = docs_changer.apply_suggestion(suggested_change)
        _apply_change(path, content)

    tracker.log()
