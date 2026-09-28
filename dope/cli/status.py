"""Show current processing status."""

import typer

from dope.cli.ui import StatusFormatter
from dope.core.utils import require_config
from dope.repositories import JsonStateRepository, SuggestionRepository

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

    docs_state = JsonStateRepository(settings.doc_state_path).load()
    code_state = JsonStateRepository(settings.code_state_path).load()
    suggestions = SuggestionRepository(settings.suggestion_state_path).get_suggestions()
    docs_scanned = len(docs_state)
    docs_summarized = sum(1 for item in docs_state.values() if item.get("summary"))
    code_scanned = len(code_state)
    code_summarized = sum(1 for item in code_state.values() if item.get("summary"))

    # Display status using formatter
    StatusFormatter.display_status(
        docs_scanned=docs_scanned,
        docs_summarized=docs_summarized,
        code_scanned=code_scanned,
        code_summarized=code_summarized,
        suggestions_count=len(suggestions.changes_to_apply),
        scope_exists=settings.scope_path.exists(),
        state_directory=settings.state_directory,
    )
