"""Shared CLI utilities and common patterns."""

from contextlib import contextmanager
from pathlib import Path

import typer

from dope.cli.ui import error, info
from dope.models.settings import Settings


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


def require_state_files(required_files: dict[str, Path], next_step: str) -> None:
    """Ensure prerequisite state files are available for a command.

    Args:
        required_files: Mapping of user-facing state names to their paths.
        next_step: Command guidance displayed when a prerequisite is missing.
    """
    missing_files = [name for name, path in required_files.items() if not path.is_file()]
    if not missing_files:
        return

    error(f"Cannot continue: missing {', '.join(missing_files)}.")
    info(next_step)
    raise typer.Exit(1)


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
        self.docs_root = settings.docs.docs_root or Path(".")
        self.code_root = settings.git.code_repo_root or Path(".")


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
    >>>         scanner = ctx.factory.doc_scanner(ctx.docs_root, ctx.tracker)
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
