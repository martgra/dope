from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn

from app import get_settings
from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.core.context import UsageContext
from app.models.constants import (
    DESCRIBE_CODE_STATE_FILENAME,
    DESCRIBE_DOCS_STATE_FILENAME,
    SUGGESTION_STATE_FILENAME,
)
from app.models.domain.scope_template import ScopeTemplate
from app.services.describer.describer_base import DescriberService
from app.services.suggester.suggester_service import DocChangeSuggester

app = typer.Typer()


@app.command()
def suggest(
    branch: Annotated[str, typer.Option("--branch", help="Branch to run againt")] = None,
):
    settings = get_settings()
    suggestor = DocChangeSuggester(
        suggestion_state_path=settings.state_directory / SUGGESTION_STATE_FILENAME,
    )
    code_scanner = DescriberService(
        GitConsumer(".", branch),
        state_filepath=settings.state_directory / DESCRIBE_CODE_STATE_FILENAME,
    )
    doc_scanner = DescriberService(
        DocConsumer(
            ".",
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
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

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Creating suggestions...", total=None)
        suggestor.get_suggestions(scope=scope, docs_change=doc_state, code_change=code_state)
    UsageContext().log_usage()
