from pathlib import Path

import yaml
from git import InvalidGitRepositoryError, Repo
from platformdirs import user_config_dir
from pydantic_settings import BaseSettings

from app.models.constants import APP_NAME


def _find_project_root(start: Path | None = None) -> Path:
    start = start or Path.cwd()
    try:
        repo = Repo(start, search_parent_directories=True)
        return Path(repo.working_tree_dir)
    except InvalidGitRepositoryError:
        return start


def locate_local_config_file(config_file_name: str) -> Path | None:
    """Return path to config file.

    Args:
        config_file_name (str): Name of config file.

    Returns:
        Path | None: Path to config file if found
    """
    start = Path.cwd()
    root = _find_project_root(start)

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
    """Return filepath to global config.

    Args:
        config_file_name (str): Name of config file.

    Returns:
        Path | None: Path to config file if exists.
    """
    config_filepath = Path(user_config_dir(APP_NAME)) / Path(config_file_name)

    if config_filepath.is_file():
        return config_filepath
    else:
        return None


def generate_global_config_file(config_filename: str, settings_to_write: BaseSettings):
    """Dump settings to global config file.

    Args:
        config_filename (str): Global config filename.
        settings_to_write (BaseSettings): Settings object.
    """
    config_filepath = Path(user_config_dir(APP_NAME)) / Path(config_filename)

    with open(config_filepath, "w", encoding="utf-8") as file:
        yaml.safe_dump(settings_to_write.model_dump(mode="json"), file, sort_keys=False)


def generate_local_config_file(config_filename, settings_to_write: BaseSettings):
    """Dump settings to local config file.

    Args:
        config_filename (str): Local config filename.
        settings_to_write (BaseSettings): Settings object.
    """
    base_path = Path.cwd()
    dope_local_config_path = base_path / Path(config_filename)

    with open(dope_local_config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(settings_to_write.model_dump(mode="json"), file, sort_keys=False)


def generate_local_cache():
    """Generate local cache folder.

    Returns:
        Path: Path to local cache dir.
    """
    cache_dir_path = Path.cwd() / Path(f".{APP_NAME}")
    cache_dir_path.mkdir(exist_ok=True)
    return cache_dir_path


def load_settings_from_yaml(config_filepath: Path):
    """Load settings from config file.

    Args:
        config_filepath (Path): Path to config file.

    Returns:
        _type_: _description_
    """
    with config_filepath.open() as file:
        return yaml.safe_load(file)


def get_graphical_repo_tree(repo_path: str) -> str:
    """Return repo structure.

    Args:
        repo_path (str): Path to repo.

    Returns:
        str: File structure of repo.
    """
    repo = Repo(repo_path)
    tree = repo.head.commit.tree

    def traverse(tree, prefix=""):
        entries = list(tree)
        lines = []
        for i, item in enumerate(entries):
            is_last = i == len(entries) - 1
            branch = "└── " if is_last else "├── "
            line = f"{prefix}{branch}{item.name}"
            lines.append(line)
            if item.type == "tree":
                extension = "    " if is_last else "│   "
                lines.extend(traverse(item, prefix + extension))
        return lines

    tree_lines = []
    for item in tree:
        if item.type == "tree":
            tree_lines.append(f"{item.name}/")
            tree_lines.extend(traverse(item, prefix=""))
        else:
            tree_lines.append(item.name)

    return "\n".join(tree_lines)
