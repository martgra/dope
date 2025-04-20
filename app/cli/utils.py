import json

import click
from pydantic.json import pydantic_encoder


def show_full_output(data: dict, print_output: bool):
    """Print full output."""
    if print_output:
        click.echo(json.dumps(data, indent=2, ensure_ascii=False, default=pydantic_encoder))
    if isinstance(data, list):
        click.echo(len(data))
    print("Done")
