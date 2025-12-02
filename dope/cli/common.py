"""Shared CLI utilities and common patterns."""

from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

import typer

from dope.models.settings import Settings


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


class CommandContext:
    """Context for command execution with automatic setup and cleanup."""

    def __init__(self, settings: Settings, tracker, branch: str | None = None):
        """Initialize command context.

        Args:
            settings: Application settings
            tracker: Usage tracker instance
            branch: Optional branch name (will be resolved to default if None)
        """
        from dope.core.service_factory import ServiceFactory

        self.settings = settings
        self.factory = ServiceFactory(settings)
        self.tracker = tracker
        self.branch = resolve_branch(branch, settings)

    def __enter__(self):
        """Enter context."""
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Exit context and log usage."""
        self.tracker.log()
        return False


@contextmanager
def command_context(branch: str | None = None):
    """Context manager for CLI commands with automatic setup and cleanup.

    Handles:
    - Configuration loading and validation
    - Usage tracker creation and automatic logging
    - Branch resolution

    Args:
        branch: Optional branch parameter (will use configured default if None)

    Yields:
        CommandContext: Context with settings, tracker, and resolved branch

    Raises:
        ConfigurationError: If no configuration found or agent not configured

    Example:
        >>> @app.command()
        >>> def scan_docs(branch: str | None = None):
        >>>     with command_context(branch=branch) as ctx:
        >>>         scanner = ctx.settings.doc_scanner(Path("."), ctx.tracker)
        >>>         scanner.scan()
        >>>     # Usage is automatically logged on exit
    """
    from dope.core.usage import UsageTracker
    from dope.core.utils import require_config

    settings = require_config()
    tracker = UsageTracker()

    ctx = CommandContext(settings, tracker, branch)
    try:
        yield ctx
    finally:
        ctx.tracker.log()
