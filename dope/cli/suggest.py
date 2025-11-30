"""Generate documentation update suggestions."""

from pathlib import Path

import typer
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn

from dope.cli.common import get_branch_option, get_state_path, resolve_branch
from dope.consumers.doc_consumer import DocConsumer
from dope.consumers.git_consumer import GitConsumer
from dope.core.usage import UsageTracker
from dope.core.utils import require_config
from dope.models.constants import (
    DESCRIBE_CODE_STATE_FILENAME,
    DESCRIBE_DOCS_STATE_FILENAME,
    SUGGESTION_STATE_FILENAME,
)
from dope.models.domain.scope import ScopeTemplate
from dope.services.describer.describer_base import CodeDescriberService, DescriberService
from dope.services.suggester.suggester_service import DocChangeSuggester

app = typer.Typer()


@app.callback(invoke_without_command=True)
def suggest(
    ctx: typer.Context,
    branch: get_branch_option() = None,
):
    """Generate documentation update suggestions based on code and doc changes."""
    if ctx.resilient_parsing:
        return

    settings = require_config()
    branch = resolve_branch(branch, settings)
    tracker = UsageTracker()

    suggestor = DocChangeSuggester(
        suggestion_state_path=get_state_path(settings, SUGGESTION_STATE_FILENAME),
        usage_tracker=tracker,
    )
    code_scanner = CodeDescriberService(
        GitConsumer(Path("."), branch),
        state_filepath=get_state_path(settings, DESCRIBE_CODE_STATE_FILENAME),
        usage_tracker=tracker,
    )
    doc_scanner = DescriberService(
        DocConsumer(
            Path("."),
            file_type_filter=settings.docs.doc_filetypes,
            exclude_dirs=settings.docs.exclude_dirs,
        ),
        state_filepath=get_state_path(settings, DESCRIBE_DOCS_STATE_FILENAME),
        usage_tracker=tracker,
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
    tracker.log()
