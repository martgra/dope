import click

from app.cli.change import change
from app.cli.config import config
from app.cli.describe import describe
from app.cli.scan import scan
from app.cli.scope import scope
from app.cli.suggest import suggest


@click.group
def cli():
    pass


def run_cli():
    cli.add_command(scan)
    cli.add_command(describe)
    cli.add_command(config)
    cli.add_command(suggest)
    cli.add_command(change)
    cli.add_command(scope)

    cli()


if __name__ == "__main__":
    run_cli()
