"""Configuration file I/O operations."""

from pathlib import Path

import yaml
from platformdirs import user_config_dir
from pydantic_settings import BaseSettings

from dope.models.constants import APP_NAME


def load_settings_from_yaml(config_filepath: Path) -> dict:
    """Load settings from YAML configuration file.

    Args:
        config_filepath: Path to YAML config file

    Returns:
        Dictionary of settings loaded from file
    """
    with config_filepath.open() as file:
        return yaml.safe_load(file)


def generate_global_config_file(config_filename: str, settings_to_write: BaseSettings) -> None:
    """Write settings to global configuration file.

    Args:
        config_filename: Name of config file
        settings_to_write: Settings object to serialize
    """
    config_filepath = Path(user_config_dir(APP_NAME)) / Path(config_filename)

    with open(config_filepath, "w", encoding="utf-8") as file:
        yaml.safe_dump(settings_to_write.model_dump(mode="json"), file, sort_keys=False)


def generate_local_config_file(config_filename: str, settings_to_write: BaseSettings) -> None:
    """Write settings to local configuration file.

    Args:
        config_filename: Name of config file
        settings_to_write: Settings object to serialize
    """
    base_path = Path.cwd()
    dope_local_config_path = base_path / Path(config_filename)

    with open(dope_local_config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            settings_to_write.model_dump(mode="json", exclude_none=True), file, sort_keys=False
        )


def generate_local_cache(cache_dir_path: Path | None = None, add_to_git: bool = False) -> Path:
    """Create local cache directory with optional gitignore.

    Args:
        cache_dir_path: Path to cache directory (defaults to .dope in current dir)
        add_to_git: If False, create .gitignore to exclude from version control

    Returns:
        Path to created cache directory
    """
    if not cache_dir_path:
        cache_dir_path = Path.cwd() / Path(f".{APP_NAME}")

    cache_dir_path.mkdir(exist_ok=True)

    if not add_to_git:
        gitignore_path = cache_dir_path / ".gitignore"
        with gitignore_path.open("w") as file:
            file.write("*")

    return cache_dir_path
