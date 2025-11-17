"""Apply suggested documentation changes."""

from pathlib import Path
from typing import Annotated

import typer

from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.core.context import UsageContext
from app.core.progress import track
from app.core.utils import require_config
from app.models.constants import SUGGESTION_STATE_FILENAME
from app.services.changer.changer_service import DocsChanger
from app.services.suggester.suggester_service import DocChangeSuggester

app = typer.Typer(help="Apply suggested documentation changes")


def _apply_change(path: Path, content: str) -> None:
    """Write changes to file, creating directories if needed."""
    path = Path(path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    # Now write (or overwrite) the file
    with path.open("w", encoding="utf-8") as file:
        file.write(content)


@app.command()
def apply(
    branch: Annotated[str, typer.Option("--branch", "-b", help="Branch to compare against")] = None,
):
    """Apply previously generated documentation suggestions to files."""
    settings = require_config()

    # Use default branch if not specified
    if branch is None:
        branch = settings.git.default_branch

    docs_changer = DocsChanger(
        docs_consumer=DocConsumer(
            ".",
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        git_consumer=GitConsumer(".", branch),
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
