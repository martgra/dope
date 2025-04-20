import json
from pathlib import Path

import click

from app import settings
from app.agents.docs_changer import agent
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.services.doc_changer_service import DocsChanger
from app.services.suggester import DocChangeSuggester


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
    "--output", is_flag=True, show_default=True, default=False, help="Output the diff to console."
)
@click.option(
    "--apply-change", is_flag=True, show_default=True, default=False, help="Apply the changes."
)
def change_doc(output, apply_change):
    docs_changer = DocsChanger(
        agent=agent,
        docs_consumer=DocConsumer(
            ".",
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        git_consumer=GitConsumer(".", settings.git.default_branch),
    )

    suggestor = DocChangeSuggester(
        agent=None, suggestion_state_path=settings.suggestion.state_filepath
    )

    suggest_state = suggestor.get_state()

    changes = docs_changer.apply_suggestions(suggest_state.changes_to_apply)
    if output:
        print(json.dumps(changes))

    if apply_change:
        _apply_change(changes)
