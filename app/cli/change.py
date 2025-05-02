from pathlib import Path
from typing import Annotated

import typer

from app import settings
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.models.constants import SUGGESTION_STATE_FILENAME
from app.services.changer.changer_service import DocsChanger
from app.services.suggester.suggester_service import DocChangeSuggester


def _apply_change(changes: dict[str, str]) -> None:
    for path_str, content in changes.items():
        path = Path(path_str)

        # Make sure the parent directory exists
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        # Now write (or overwrite) the file
        with path.open("w", encoding="utf-8") as file:
            file.write(content)


app = typer.Typer()


@app.command()
def change(
    branch: Annotated[str, typer.Option(help="Branch to run againt")] = settings.git.default_branch,
):
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

    changes = docs_changer.apply_suggestions(suggest_state.changes_to_apply)
    _apply_change(changes)
