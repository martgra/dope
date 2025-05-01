from pathlib import Path

import click
import yaml

from app import settings
from app.cli.utils import show_full_output
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.models.constants import (
    DESCRIBE_CODE_STATE_FILENAME,
    DESCRIBE_DOCS_STATE_FILENAME,
    SUGGESTION_STATE_FILENAME,
)
from app.models.domain.scope_template import ScopeTemplate
from app.services.describer.describer_service import Scanner
from app.services.suggester.suggester_service import DocChangeSuggester


@click.group(name="suggest")
def suggest():
    pass


@suggest.command(name="docs")
@click.option(
    "--output", is_flag=True, show_default=True, default=False, help="Output the diff to console."
)
@click.option(
    "--branch", default=settings.git.default_branch, help="Branch to find changes against."
)
def suggest_code_change(output, branch: str):
    suggestor = DocChangeSuggester(
        suggestion_state_path=settings.state_directory / SUGGESTION_STATE_FILENAME,
    )
    code_scanner = Scanner(
        GitConsumer(".", branch),
        None,
        state_filepath=settings.state_directory / DESCRIBE_CODE_STATE_FILENAME,
    )
    doc_scanner = Scanner(
        DocConsumer(
            ".",
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        None,
        state_filepath=settings.state_directory / DESCRIBE_DOCS_STATE_FILENAME,
    )
    doc_state = doc_scanner.get_state()
    code_state = code_scanner.get_state()

    scope_path = Path(settings.state_directory / "scope.yaml")
    if scope_path.is_file():
        with scope_path.open() as file:
            scope = ScopeTemplate(**yaml.safe_load(file)).model_dump_json(indent=2)

    else:
        scope = ""
    suggestions = (
        suggestor.get_suggestions(scope=scope, docs_change=doc_state, code_change=code_state),
    )
    show_full_output(suggestions, output)
