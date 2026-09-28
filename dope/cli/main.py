"""DOPE - AI-powered documentation management CLI."""

import typer

from dope.cli import apply, config, scan, scope, status, suggest, update
from dope.exceptions import DopeError


def run_cli():
    """Main CLI entry point."""
    app = typer.Typer(
        no_args_is_help=True,
        help="DOPE - AI-powered documentation management",
        epilog="""
Quick Start:
  1. dope config init              # Configure LLM provider
  2. dope update                   # Scan and preview documentation updates
  3. dope update --apply           # Apply the generated updates
  4. dope status                   # Check current state

Advanced Workflow:
  1. dope scan docs && dope scan code
  2. dope suggest
  3. dope apply

Run 'dope COMMAND --help' for more information on a command.
        """,
    )

    # Add command groups
    app.add_typer(update.app, name="update")
    app.add_typer(scan.app, name="scan")
    app.add_typer(suggest.app, name="suggest")
    app.add_typer(apply.app, name="apply")
    app.add_typer(status.app, name="status")
    app.add_typer(scope.app, name="scope")
    app.add_typer(config.app, name="config")

    try:
        app()
    except DopeError as error:
        from rich import print as rprint

        rprint(f"[red]Error: {error}[/red]")
        raise typer.Exit(1) from error


if __name__ == "__main__":
    run_cli()
