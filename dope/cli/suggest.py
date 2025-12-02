"""Generate documentation update suggestions."""

from pathlib import Path

import typer

from dope.cli.common import command_context, get_branch_option
from dope.cli.ui import ProgressReporter

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

        # Generate suggestions with progress indicator
        with ProgressReporter.spinner("Generating suggestions...") as progress:
            progress.add_task(description="Generating suggestions...", total=None)
            suggester.get_suggestions(docs_change=doc_state, code_change=code_state)
