"""Generate documentation update suggestions."""

from pathlib import Path

import typer
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn

from dope.cli.common import get_branch_option, resolve_branch
from dope.cli.factories import create_code_scanner, create_doc_scanner, create_suggester
from dope.core.usage import UsageTracker
from dope.core.utils import require_config
from dope.models.domain.scope import ScopeTemplate

app = typer.Typer()


def _load_scope(settings) -> str:
    """Load scope template if available.

    Args:
        settings: Application settings

    Returns:
        Scope as JSON string, or empty string if not found
    """
    scope_path = Path(settings.state_directory / "scope.yaml")
    if scope_path.is_file():
        with scope_path.open() as file:
            return ScopeTemplate(**yaml.safe_load(file)).model_dump_json(indent=2)
    return ""


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

    # Create services using factories
    suggester = create_suggester(settings, tracker)
    code_scanner = create_code_scanner(Path("."), branch, settings, tracker)
    doc_scanner = create_doc_scanner(Path("."), settings, tracker)

    # Get current state
    doc_state = doc_scanner.get_state()
    code_state = code_scanner.get_state()
    scope = _load_scope(settings)

    # Generate suggestions with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Generating suggestions...", total=None)
        suggester.get_suggestions(scope=scope, docs_change=doc_state, code_change=code_state)

    tracker.log()
