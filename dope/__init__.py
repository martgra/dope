from dope.core.config_locator import locate_global_config, locate_local_config_file
from dope.models.constants import CONFIG_FILENAME
from dope.models.settings import Settings, get_settings

# Locate config file for reference (doesn't load settings yet)
config_filepath = locate_local_config_file(CONFIG_FILENAME) or locate_global_config(CONFIG_FILENAME)

__all__ = ["Settings", "get_settings", "config_filepath"]
