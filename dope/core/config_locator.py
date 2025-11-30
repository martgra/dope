"""Configuration file location utilities."""

from pathlib import Path

from git import InvalidGitRepositoryError, Repo
from platformdirs import user_config_dir

from dope.models.constants import APP_NAME


def find_project_root(start: Path | None = None) -> Path:
    """Find project root by searching for Git repository.

    Args:
        start: Starting directory for search (defaults to current directory)

    Returns:
        Path to project root, or start path if not a Git repository
    """
    start = start or Path.cwd()
    try:
        repo = Repo(start, search_parent_directories=True)
        return Path(repo.working_tree_dir) if repo.working_tree_dir else start
    except InvalidGitRepositoryError:
        return start


def locate_local_config_file(config_file_name: str) -> Path | None:
    """Locate configuration file in project hierarchy.

    Searches from current directory up to project root.

    Args:
        config_file_name: Name of configuration file to find

    Returns:
        Path to config file if found, None otherwise
    """
    start = Path.cwd()
    root = find_project_root(start)

    current = start.resolve()
    root = root.resolve()

    while True:
        candidate = current / config_file_name
        if candidate.is_file():
            return candidate
        if current == root:
            break
        current = current.parent

    return None


def locate_global_config(config_file_name: str) -> Path | None:
    """Locate global configuration file in user config directory.

    Args:
        config_file_name: Name of configuration file

    Returns:
        Path to global config file if it exists, None otherwise
    """
    config_filepath = Path(user_config_dir(APP_NAME)) / Path(config_file_name)

    if config_filepath.is_file():
        return config_filepath
    return None
