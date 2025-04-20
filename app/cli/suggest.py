import click

from app import settings
from app.agents.docs_change_suggester import agent
from app.cli.utils import show_full_output
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.services.scanner import Scanner
from app.services.suggester import DocChangeSuggester


@click.group(name="suggest")
def suggest():
    pass


@suggest.command(name="docs")
@click.option(
    "--output", is_flag=True, show_default=True, default=False, help="Output the diff to console."
)
def suggest_code_change(output):
    suggestor = DocChangeSuggester(
        agent=agent, suggestion_state_path=settings.suggestion.state_filepath
    )
    code_scanner = Scanner(
        GitConsumer(".", settings.git.default_branch),
        None,
        state_filepath=settings.git.state_filepath,
    )
    doc_scanner = Scanner(
        DocConsumer(
            ".",
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        None,
        state_filepath=settings.docs.state_filepath,
    )
    doc_state = doc_scanner.get_state()
    code_state = code_scanner.get_state()

    show_full_output(
        suggestor.get_suggestions(docs_change=doc_state, code_change=code_state), output
    )
