"""Generate documentation update suggestions."""

from pathlib import Path

import typer
import yaml

from dope.cli.common import command_context, get_branch_option
from dope.cli.ui import ProgressReporter
from dope.models.domain.scope import ScopeTemplate

app = typer.Typer(
    epilog="""
Examples:
  # Generate suggestions using configured branch
  $ dope suggest

  # Generate suggestions against specific branch
  $ dope suggest --branch develop

  # Workflow: scan first, then suggest
  $ dope scan docs && dope scan code
  $ dope suggest
    """
)


def _load_scope(settings) -> str:
    """Load scope template if available.

    Args:
        settings: Application settings

    Returns:
        Scope as JSON string, or empty string if not found
    """
    if settings.scope_path.is_file():
        with settings.scope_path.open() as file:
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

    with command_context(branch=branch) as cmd_ctx:
        # Create services
        suggester = cmd_ctx.factory.suggester(cmd_ctx.tracker)
        code_scanner = cmd_ctx.factory.code_scanner(Path("."), cmd_ctx.branch, cmd_ctx.tracker)
        doc_scanner = cmd_ctx.factory.doc_scanner(Path("."), cmd_ctx.tracker)

        # Get current state
        doc_state = doc_scanner.get_state()
        code_state = code_scanner.get_state()
        scope = _load_scope(cmd_ctx.settings)

        # Generate suggestions with progress indicator
        with ProgressReporter.spinner("Generating suggestions...") as progress:
            progress.add_task(description="Generating suggestions...", total=None)
            suggester.get_suggestions(scope=scope, docs_change=doc_state, code_change=code_state)
