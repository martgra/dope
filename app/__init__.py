from app.core.settings import Settings
from app.core.utils import (
    generate_global_config_file,
    load_settings_from_yaml,
    locate_global_config,
    locate_local_config_file,
)
from app.models.constants import CONFIG_FILENAME

config_filepath = locate_local_config_file(CONFIG_FILENAME) or locate_global_config(CONFIG_FILENAME)

settings = (
    Settings() if config_filepath is None else Settings(**load_settings_from_yaml(config_filepath))
)

if config_filepath is None:
    generate_global_config_file(CONFIG_FILENAME, settings)
