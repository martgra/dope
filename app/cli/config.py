from typing import Annotated

import typer
from rich import print

from app import settings
from app.core.settings import Settings
from app.core.utils import (
    generate_local_cache,
    generate_local_config_file,
    locate_local_config_file,
)
from app.models.constants import CONFIG_FILENAME
from app.models.enums import Provider

app = typer.Typer()


@app.command()
def show():
    print(settings.model_dump(mode="json"))


@app.command()
def init(
    all_default: Annotated[bool, typer.Option("--yes", help="All default values")] = True,
    force: Annotated[bool, typer.Option("--force", help="Override existing config")] = False,
    provider: Annotated[
        Provider, typer.Option(help="Choose LLM provider to use")
    ] = Provider.OPENAI,
):
    """Initialize a YAML config file for Dope CLI."""
    local_config_path = locate_local_config_file(CONFIG_FILENAME)
    if not local_config_path or force:
        dope_cache_dir = generate_local_cache()
        local_settings = Settings(state_directory=dope_cache_dir)
        generate_local_config_file(CONFIG_FILENAME, local_settings)
    else:
        print(f"Found local config in repo at {local_config_path}. Skipping")
