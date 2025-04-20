import click

from app import settings


@click.group(name="config")
def config():
    pass


@config.command(name="show")
def config_show():
    click.echo(settings.model_dump_json(indent=2))
