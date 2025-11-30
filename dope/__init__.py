from dope.core.settings import Settings
from dope.core.utils import (
    load_settings_from_yaml,
    locate_global_config,
    locate_local_config_file,
)
from dope.models.constants import CONFIG_FILENAME

config_filepath = locate_local_config_file(CONFIG_FILENAME) or locate_global_config(CONFIG_FILENAME)

# Always create settings object - agent will be None if no config
settings = Settings()
if config_filepath:
    try:
        settings = Settings(**load_settings_from_yaml(config_filepath))
    except Exception as e:
        # Config exists but is invalid - this is an error
        import sys

        from rich import print as rprint

        rprint(f"[red]❌ Config file invalid: {config_filepath}[/red]")
        rprint(f"[yellow]Error: {e}[/yellow]")
        rprint("[blue]Run 'dope config init --force' to recreate[/blue]")
        sys.exit(1)
