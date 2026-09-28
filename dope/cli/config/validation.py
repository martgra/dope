"""Configuration validation logic."""

from git import InvalidGitRepositoryError, Repo
from rich.console import Console

from dope.models.enums import Provider
from dope.models.settings import Settings

console = Console()


def validate_config(settings: Settings) -> tuple[list[str], list[str]]:
    """Validate configuration settings.

    Args:
        settings: Settings object to validate

    Returns:
        Tuple of (errors, warnings) lists
    """
    errors = []
    warnings = []

    # Check state directory
    if not settings.state_directory.exists():
        warnings.append(f"State directory doesn't exist: {settings.state_directory}")

    # Check git repo
    if settings.git.code_repo_root:
        try:
            repo = Repo(str(settings.git.code_repo_root))
            # Check if branch exists
            branches = [str(b) for b in repo.branches]
            if settings.git.default_branch not in branches:
                errors.append(
                    f"Branch '{settings.git.default_branch}' not found in repo. "
                    f"Available: {', '.join(branches[:5])}"
                )
        except InvalidGitRepositoryError:
            errors.append(f"Not a git repository: {settings.git.code_repo_root}")

    # Check docs root
    if settings.docs.docs_root and not settings.docs.docs_root.exists():
        errors.append(f"Docs root doesn't exist: {settings.docs.docs_root}")

    # Check LLM configuration
    agent = settings.agent
    if agent is None:
        errors.append("LLM agent not configured")
    elif not agent.token:
        errors.append("LLM token not configured")
    elif agent.provider == Provider.AZURE and not agent.base_url:
        errors.append("Azure provider requires base_url to be set")

    return errors, warnings


def display_validation_results(errors: list[str], warnings: list[str]) -> bool:
    """Display validation results to console.

    Args:
        errors: List of error messages
        warnings: List of warning messages

    Returns:
        True if valid (no errors), False otherwise
    """
    if errors:
        console.print("\n[red]❌ Configuration has errors:[/red]")
        for error in errors:
            console.print(f"  • {error}")

    if warnings:
        console.print("\n[yellow]⚠️  Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  • {warning}")

    if not errors and not warnings:
        console.print("\n[green]✅ Configuration is valid![/green]")
        return True

    if errors:
        console.print("\n[blue]💡 Run 'dope config init --force' to fix[/blue]")
        return False

    return True
