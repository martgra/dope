import typer
from pydantic import BaseModel

from app import get_settings
from app.cli import change, config, describe, scope, suggest
from app.core.settings import Settings


class CliContext(BaseModel):
    """Cli context class."""

    settings: Settings | None = None


def run_cli():
    app = typer.Typer(no_args_is_help=True)

    @app.callback(
        invoke_without_command=True,
        help="Global options for all commands",
    )
    def global_function(ctx: typer.Context):
        ctx.ensure_object(CliContext)
        ctx.obj.settings = get_settings()

    app.add_typer(scope.app, name="scope")
    app.add_typer(config.app, name="config")
    app.add_typer(change.app)
    app.add_typer(describe.app, name="describe")
    app.add_typer(suggest.app)
    app()


if __name__ == "__main__":
    run_cli()
