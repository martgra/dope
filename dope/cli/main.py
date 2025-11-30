"""DOPE - AI-powered documentation management CLI."""

import typer

from dope.cli import apply, config, scan, scope, status, suggest


def run_cli():
    """Main CLI entry point."""
    app = typer.Typer(
        no_args_is_help=True,
        help="DOPE - AI-powered documentation management",
        epilog="Run 'dope COMMAND --help' for more information on a command.",
    )

    # Add command groups
    app.add_typer(scan.app, name="scan")
    app.add_typer(suggest.app, name="suggest")
    app.add_typer(apply.app, name="apply")
    app.add_typer(status.app, name="status")
    app.add_typer(scope.app, name="scope")
    app.add_typer(config.app, name="config")

    app()


if __name__ == "__main__":
    run_cli()
