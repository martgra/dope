from app.core.settings import Settings
from app.core.utils import (
    load_settings_from_yaml,
    locate_global_config,
    locate_local_config_file,
)
from app.models.constants import CONFIG_FILENAME

config_filepath = locate_local_config_file(CONFIG_FILENAME) or locate_global_config(CONFIG_FILENAME)

# Don't crash if no config exists - let commands handle it
settings = None
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
