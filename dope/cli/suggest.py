"""Generate documentation update suggestions."""

from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn

from dope.consumers.doc_consumer import DocConsumer
from dope.consumers.git_consumer import GitConsumer
from dope.core.context import UsageContext
from dope.core.utils import require_config
from dope.models.constants import (
    DESCRIBE_CODE_STATE_FILENAME,
    DESCRIBE_DOCS_STATE_FILENAME,
    SUGGESTION_STATE_FILENAME,
)
from dope.models.domain.scope_template import ScopeTemplate
from dope.services.describer.describer_base import DescriberService
from dope.services.suggester.suggester_service import DocChangeSuggester

app = typer.Typer(help="Generate documentation update suggestions")


@app.command()
def suggest(
    branch: Annotated[str, typer.Option("--branch", "-b", help="Branch to compare against")] = None,
):
    """Generate documentation update suggestions based on code and doc changes."""
    settings = require_config()

    # Use default branch if not specified
    if branch is None:
        branch = settings.git.default_branch

    suggestor = DocChangeSuggester(
        suggestion_state_path=settings.state_directory / SUGGESTION_STATE_FILENAME,
    )
    code_scanner = DescriberService(
        GitConsumer(".", branch),
        None,
        state_filepath=settings.state_directory / DESCRIBE_CODE_STATE_FILENAME,
    )
    doc_scanner = DescriberService(
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

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Generating suggestions...", total=None)
        suggestor.get_suggestions(scope=scope, docs_change=doc_state, code_change=code_state)
    UsageContext().log_usage()
