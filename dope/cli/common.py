"""Shared CLI utilities and common patterns."""

from pathlib import Path
from typing import Annotated

import typer

from dope.core.settings import Settings


def get_branch_option() -> type[str | None]:
    """Create standardized branch option annotation for CLI commands.

    Returns:
        Type annotation for branch parameter with consistent help text

    Example:
        >>> @app.command()
        >>> def my_command(branch: Annotated[str | None, get_branch_option()] = None):
        >>>     branch = resolve_branch(branch, settings)
    """
    return Annotated[
        str | None,
        typer.Option(
            "--branch",
            "-b",
            help="Branch to compare against (defaults to configured branch)",
        ),
    ]


def resolve_branch(branch: str | None, settings: Settings) -> str:
    """Resolve branch parameter to actual branch name.

    Args:
        branch: Branch name from CLI argument, or None
        settings: Application settings containing default branch

    Returns:
        Resolved branch name (parameter value or settings default)

    Example:
        >>> settings = Settings(git=CodeRepoSettings(default_branch="main"))
        >>> resolve_branch(None, settings)
        'main'
        >>> resolve_branch("develop", settings)
        'develop'
    """
    return branch if branch is not None else settings.git.default_branch


def get_state_path(settings: Settings, filename: str) -> Path:
    """Get full path to a state file.

    Args:
        settings: Application settings containing state directory
        filename: Name of the state file

    Returns:
        Full absolute path to state file

    Example:
        >>> settings = Settings(state_directory=Path(".dope"))
        >>> get_state_path(settings, "doc-state.json")
        Path('.dope/doc-state.json')
    """
    return settings.state_directory / filename
