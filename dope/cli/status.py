"""Show current processing status."""

import json

import typer

from dope.cli.ui import StatusFormatter
from dope.core.utils import require_config

app = typer.Typer(
    help="Show current processing status",
    epilog="""
Examples:
  # Check current state of all components
  $ dope status
    """,
)


@app.command()
def status():
    """Show current status of scanned files and suggestions."""
    settings = require_config()

    # Load state files using properties
    docs_state_path = settings.doc_state_path
    code_state_path = settings.code_state_path
    suggestions_state_path = settings.suggestion_state_path
    scope_path = settings.scope_path

    # Count items in each state
    docs_scanned = 0
    docs_summarized = 0
    if docs_state_path.exists():
        with docs_state_path.open() as f:
            docs_state = json.load(f)
            docs_scanned = len(docs_state)
            docs_summarized = sum(1 for item in docs_state.values() if item.get("summary"))

    code_scanned = 0
    code_summarized = 0
    if code_state_path.exists():
        with code_state_path.open() as f:
            code_state = json.load(f)
            code_scanned = len(code_state)
            code_summarized = sum(1 for item in code_state.values() if item.get("summary"))

    suggestions_count = 0
    if suggestions_state_path.exists():
        with suggestions_state_path.open() as f:
            suggestions_state = json.load(f)
            suggestions_count = len(suggestions_state.get("changes_to_apply", []))

    scope_exists = scope_path.exists()

    # Display status using formatter
    StatusFormatter.display_status(
        docs_scanned=docs_scanned,
        docs_summarized=docs_summarized,
        code_scanned=code_scanned,
        code_summarized=code_summarized,
        suggestions_count=suggestions_count,
        scope_exists=scope_exists,
        state_directory=settings.state_directory,
    )
