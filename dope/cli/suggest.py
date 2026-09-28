"""Generate documentation update suggestions."""

from typing import Annotated

import typer

from dope.cli.common import command_context, require_state_files
from dope.cli.ui import ProgressReporter, success, warning

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
    branch: Annotated[
        str | None,
        typer.Option(
            "--branch",
            "-b",
            help="Branch to compare against (defaults to configured branch)",
        ),
    ] = None,
):
    """Generate documentation update suggestions based on code and doc changes."""
    if ctx.resilient_parsing:
        return

    with command_context(branch=branch) as cmd_ctx:
        require_state_files(
            {
                "documentation scan state": cmd_ctx.settings.doc_state_path,
                "code scan state": cmd_ctx.settings.code_state_path,
            },
            "Run 'dope scan docs' and 'dope scan code', or use 'dope update'.",
        )

        # Create services
        suggester = cmd_ctx.factory.suggester(cmd_ctx.tracker)
        code_scanner = cmd_ctx.factory.code_scanner(
            cmd_ctx.code_root, cmd_ctx.branch, cmd_ctx.tracker
        )
        doc_scanner = cmd_ctx.factory.doc_scanner(cmd_ctx.docs_root, cmd_ctx.tracker)

        # Get current state
        doc_state = doc_scanner.get_state()
        code_state = code_scanner.get_state()

        # Generate suggestions with progress indicator
        with ProgressReporter.spinner("Generating suggestions...") as progress:
            progress.add_task(description="Generating suggestions...", total=None)
            suggestions = suggester.get_suggestions(docs_change=doc_state, code_change=code_state)

        suggestion_count = len(suggestions.changes_to_apply)
        if suggestion_count:
            success(f"Generated {suggestion_count} documentation suggestions. Run 'dope apply'.")
        else:
            warning("No documentation updates are needed for the scanned changes.")
