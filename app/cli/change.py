import json
from pathlib import Path

import click

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


@click.group(name="change")
def change():
    pass


@change.command(name="docs")
@click.option(
    "--output",
    is_flag=True,
    show_default=True,
    default=False,
    help="Output the changes to console.",
)
@click.option("--apply", is_flag=True, show_default=True, default=False, help="Apply the changes.")
@click.option(
    "--branch", default=settings.git.default_branch, help="Branch to find changes against."
)
def change_doc(output, apply, branch: str):
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
    if output:
        print(json.dumps(changes))

    if apply:
        _apply_change(changes)
