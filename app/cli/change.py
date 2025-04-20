import json

import click

from app import settings
from app.agents.docs_changer import agent
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.services.doc_changer_service import DocsChanger
from app.services.suggester import DocChangeSuggester


@click.group(name="change")
def change():
    pass


@change.command(name="docs")
@click.option(
    "--output", is_flag=True, show_default=True, default=False, help="Output the diff to console."
)
def change_doc(output):
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
    print(json.dumps(changes))
