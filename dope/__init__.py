from dope.core.config_locator import locate_global_config, locate_local_config_file
from dope.core.settings import Settings, get_settings
from dope.models.constants import CONFIG_FILENAME

# Locate config file for reference (doesn't load settings yet)
config_filepath = locate_local_config_file(CONFIG_FILENAME) or locate_global_config(CONFIG_FILENAME)

# DEPRECATED: Module-level settings object for backward compatibility
# Use get_settings() instead to get cached settings
settings = None

__all__ = ["Settings", "get_settings", "settings", "config_filepath"]
