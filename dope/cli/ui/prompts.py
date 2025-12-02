"""Interactive prompts using questionary."""

import functools
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import questionary
from git import Repo
from pydantic import HttpUrl, SecretStr, ValidationError
from questionary import Choice

from dope.models.constants import DEFAULT_DOC_SUFFIX, DOC_SUFFIX, EXCLUDE_DIRS
from dope.models.enums import Provider
from dope.models.shared import FileSuffix


def handle_questionary_abort(func):
    """Decorator to handle questionary abort gracefully."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = None
        try:
            result = func(*args, **kwargs)
        except KeyboardInterrupt:
            pass
        except Exception as err:
            raise err
        finally:
            if result is None:
                sys.exit(0)
        return result

    return wrapper


def text_input(message: str, default: str = "", validate: Callable | None = None) -> str:
    """Prompt for text input.

    Args:
        message: Prompt message
        default: Default value
        validate: Optional validation function

    Returns:
        User input string
    """
    return questionary.text(message=message, default=default, validate=validate).ask()


def select(message: str, choices: list, default: str | None = None) -> Any:
    """Prompt for selection from choices.

    Args:
        message: Prompt message
        choices: List of choices
        default: Default selection

    Returns:
        Selected value
    """
    return questionary.select(message=message, choices=choices, default=default).ask()


def confirm(message: str) -> bool:
    """Prompt for yes/no confirmation.

    Args:
        message: Prompt message

    Returns:
        True if confirmed, False otherwise
    """
    return questionary.confirm(message).ask()


@handle_questionary_abort
def prompt_doc_root() -> Path:
    """Prompt for documentation root directory."""
    return Path(
        questionary.path(
            "Set path to doc root folder", only_directories=True, default=str(Path(".").resolve())
        ).ask()
    )


@handle_questionary_abort
def prompt_doc_types() -> set[FileSuffix]:
    """Prompt for documentation file types."""
    choices = [
        Choice(title=suffix, value=suffix, checked=suffix in DEFAULT_DOC_SUFFIX)
        for suffix in sorted(DOC_SUFFIX)
    ]
    return set(questionary.checkbox("Select doc file types.", choices=choices).ask())


@handle_questionary_abort
def prompt_provider() -> Provider:
    """Prompt for LLM provider selection."""
    return questionary.select(
        message="Which LLM provider?",
        choices=[Choice(title=provider.value, value=provider) for provider in Provider],
    ).ask()


@handle_questionary_abort
def prompt_exclude_folders(doc_root: Path) -> set[str]:
    """Prompt for folders to exclude from documentation scanning."""
    doc_root = Path(doc_root)

    def _check_folder(file: Path):
        if file.name.startswith("."):
            return True
        return file.name in EXCLUDE_DIRS

    choices = [
        Choice(title=file.name, value=file.name, checked=_check_folder(file))
        for file in doc_root.iterdir()
        if file.is_dir()
    ]
    if choices:
        result = questionary.checkbox(
            message="Select folders to exclude from doc scan", choices=choices
        )
        return set(result.ask())
    return set()


@handle_questionary_abort
def prompt_default_branch(repo_path: str) -> str:
    """Prompt for default Git branch selection."""
    repo = Repo(str(repo_path), search_parent_directories=True)
    branches = [str(branch) for branch in repo.branches]
    return questionary.select("Select default branch", choices=branches, default="main").ask()


@handle_questionary_abort
def prompt_code_repo_root() -> Path:
    """Prompt for code repository root directory."""
    suggested_root = Repo(".", search_parent_directories=True)
    return Path(
        questionary.path(
            "Set path to code root folder",
            only_directories=True,
            default=str(Path(suggested_root.working_dir).resolve()),
        ).ask()
    )


def validate_url(text: str) -> bool | str:
    """Validate URL format."""
    try:
        HttpUrl(url=text)
        return True
    except ValidationError as e:
        msg = e.errors()[0]["msg"]
        return f"🚫 {msg}"


@handle_questionary_abort
def prompt_deployment_endpoint() -> str:
    """Prompt for Azure deployment URL."""
    return questionary.text(message="Azure deployment URL:", validate=validate_url).ask()


@handle_questionary_abort
def prompt_token() -> SecretStr:
    """Prompt for API token."""
    return SecretStr(questionary.password("Input API token").ask())


@handle_questionary_abort
def prompt_state_directory() -> Path:
    """Prompt for state directory path."""
    cache_dir = Path(".") / Path(".dope")
    return Path(
        questionary.path("Set state directory path", default=str(cache_dir.resolve())).ask()
    )


@handle_questionary_abort
def prompt_add_cache_to_git() -> bool:
    """Prompt whether to add cache directory to Git."""
    return questionary.confirm("Add cache dir to git?").ask()
