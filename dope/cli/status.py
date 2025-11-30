"""Show current processing status."""

import json

import typer
from rich.console import Console
from rich.table import Table

from dope.core.utils import require_config
from dope.models.constants import (
    DESCRIBE_CODE_STATE_FILENAME,
    DESCRIBE_DOCS_STATE_FILENAME,
    SUGGESTION_STATE_FILENAME,
)

app = typer.Typer(help="Show current processing status")
console = Console()


@app.command()
def status():
    """Show current status of scanned files and suggestions."""
    settings = require_config()

    # Load state files
    docs_state_path = settings.state_directory / DESCRIBE_DOCS_STATE_FILENAME
    code_state_path = settings.state_directory / DESCRIBE_CODE_STATE_FILENAME
    suggestions_state_path = settings.state_directory / SUGGESTION_STATE_FILENAME
    scope_path = settings.state_directory / "scope.yaml"

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

    # Create status table
    table = Table(title="DOPE Status", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")

    # Documentation status
    if docs_scanned > 0:
        table.add_row(
            "Documentation Files",
            f"{docs_summarized}/{docs_scanned} scanned and summarized",
        )
    else:
        table.add_row("Documentation Files", "[dim]Not scanned yet[/dim]")

    # Code status
    if code_scanned > 0:
        table.add_row("Code Files", f"{code_summarized}/{code_scanned} scanned and summarized")
    else:
        table.add_row("Code Files", "[dim]Not scanned yet[/dim]")

    # Suggestions status
    if suggestions_count > 0:
        table.add_row("Suggestions", f"{suggestions_count} ready to apply")
    else:
        table.add_row("Suggestions", "[dim]No suggestions generated[/dim]")

    # Scope status
    if scope_exists:
        table.add_row("Documentation Scope", "✓ Configured")
    else:
        table.add_row("Documentation Scope", "[dim]Not configured[/dim]")

    console.print(table)

    # Show next steps
    console.print("\n[bold cyan]Next Steps:[/bold cyan]")
    if docs_scanned == 0:
        console.print("  1. Run [blue]dope scan docs[/blue] to scan documentation")
    if code_scanned == 0:
        console.print("  2. Run [blue]dope scan code[/blue] to scan code changes")
    if suggestions_count == 0 and (docs_scanned > 0 or code_scanned > 0):
        console.print("  3. Run [blue]dope suggest[/blue] to generate suggestions")
    if suggestions_count > 0:
        console.print("  4. Run [blue]dope apply[/blue] to apply suggestions")

    # Show state directory
    console.print(f"\n📁 State directory: [blue]{settings.state_directory}[/blue]")
