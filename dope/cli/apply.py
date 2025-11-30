"""Apply suggested documentation changes."""

from pathlib import Path
from typing import Annotated

import typer

from dope.consumers.doc_consumer import DocConsumer
from dope.consumers.git_consumer import GitConsumer
from dope.core.context import UsageContext
from dope.core.progress import track
from dope.core.utils import require_config
from dope.models.constants import SUGGESTION_STATE_FILENAME
from dope.services.changer.changer_service import DocsChanger
from dope.services.suggester.suggester_service import DocChangeSuggester

app = typer.Typer()


def _apply_change(path: Path, content: str) -> None:
    """Write changes to file, creating directories if needed."""
    path = Path(path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    # Now write (or overwrite) the file
    with path.open("w", encoding="utf-8") as file:
        file.write(content)


@app.callback(invoke_without_command=True)
def apply(
    ctx: typer.Context,
    branch: Annotated[
        str | None, typer.Option("--branch", "-b", help="Branch to compare against")
    ] = None,
):
    """Apply previously generated documentation suggestions to files."""
    if ctx.resilient_parsing:
        return

    settings = require_config()

    # Use default branch if not specified
    if branch is None:
        branch = settings.git.default_branch

    docs_changer = DocsChanger(
        docs_consumer=DocConsumer(
            Path("."),
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        git_consumer=GitConsumer(Path("."), branch),
    )

    suggestor = DocChangeSuggester(
        suggestion_state_path=settings.state_directory / SUGGESTION_STATE_FILENAME
    )
    suggest_state = suggestor.get_state()

    for suggested_change in track(
        suggest_state.changes_to_apply, description="Applying documentation changes"
    ):
        path, content = docs_changer.apply_suggestion(suggested_change)
        _apply_change(path, content)
    UsageContext().log_usage()
