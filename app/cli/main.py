import typer

from app.cli import change, config, describe, scope, suggest


def run_cli():
    app = typer.Typer(no_args_is_help=True)
    app.add_typer(scope.app, name="scope")
    app.add_typer(config.app, name="config")
    app.add_typer(change.app)
    app.add_typer(describe.app, name="describe")
    app.add_typer(suggest.app)

    app()


if __name__ == "__main__":
    run_cli()
