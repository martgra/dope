from pathlib import Path
from typing import Annotated

import typer
import yaml

from app import settings
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

app = typer.Typer()


@app.command()
def suggest(
    branch: Annotated[
        str, typer.Option("--branch", help="Branch to run againt")
    ] = settings.git.default_branch,
):
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

    suggestor.get_suggestions(scope=scope, docs_change=doc_state, code_change=code_state)
