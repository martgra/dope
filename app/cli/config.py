import click

from app import settings
from app.core.settings import Settings
from app.core.utils import (
    generate_local_cache,
    generate_local_config_file,
    locate_local_config_file,
)
from app.models.constants import CONFIG_FILENAME


@click.group(name="config")
def config():
    pass


@config.command(name="show")
def config_show():
    click.echo(settings.model_dump_json(indent=2))


@config.command("init")
@click.option("--yes", "all_default", is_flag=True, help="Init config with all defaults")
@click.option("--force", "force", is_flag=True, help="Override existing config")
@click.option(
    "--provider", type=click.Choice(["openai", "azure"], case_sensitive=False), default="openai"
)
def init_config(all_default: bool, provider: str, force: bool):
    """Initialize a YAML config file for Dope CLI."""
    local_config_path = locate_local_config_file(CONFIG_FILENAME)
    if not local_config_path or force:
        dope_cache_dir = generate_local_cache()
        local_settings = Settings(state_directory=dope_cache_dir)
        generate_local_config_file(CONFIG_FILENAME, local_settings)
    else:
        print(f"Found local config in repo at {local_config_path}. Skipping")
