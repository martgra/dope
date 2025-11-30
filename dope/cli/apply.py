"""Apply suggested documentation changes."""

from pathlib import Path

import typer

from dope.cli.common import get_branch_option, get_state_path, resolve_branch
from dope.consumers.doc_consumer import DocConsumer
from dope.consumers.git_consumer import GitConsumer
from dope.core.progress import track
from dope.core.usage import UsageTracker
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
    branch: get_branch_option() = None,
):
    """Apply previously generated documentation suggestions to files."""
    if ctx.resilient_parsing:
        return

    settings = require_config()
    branch = resolve_branch(branch, settings)
    tracker = UsageTracker()

    docs_changer = DocsChanger(
        docs_consumer=DocConsumer(
            Path("."),
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        git_consumer=GitConsumer(Path("."), branch),
        usage_tracker=tracker,
    )

    suggestor = DocChangeSuggester(
        suggestion_state_path=get_state_path(settings, SUGGESTION_STATE_FILENAME)
    )
    suggest_state = suggestor.get_state()

    for suggested_change in track(
        suggest_state.changes_to_apply, description="Applying documentation changes"
    ):
        path, content = docs_changer.apply_suggestion(suggested_change)
        _apply_change(path, content)
    tracker.log()
