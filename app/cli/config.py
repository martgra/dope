"""Configuration management commands."""

import functools
import sys
from pathlib import Path
from typing import Annotated

import questionary
import typer
from git import InvalidGitRepositoryError, Repo
from pydantic import HttpUrl, SecretStr, ValidationError
from questionary import Choice
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from app.core.settings import AgentSettings, CodeRepoSettings, DocSettings, Settings
from app.core.utils import (
    generate_local_cache,
    generate_local_config_file,
    locate_local_config_file,
    require_config,
)
from app.models.constants import (
    CONFIG_FILENAME,
    DEFAULT_DOC_SUFFIX,
    DOC_SUFFIX,
    EXCLUDE_DIRS,
)
from app.models.enums import Provider
from app.models.internal import FileSuffix

app = typer.Typer(help="Manage application configuration")
console = Console()


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


@handle_questionary_abort
def _set_doc_root() -> str:
    return Path(
        questionary.path(
            "Set path to doc root folder", only_directories=True, default=str(Path(".").resolve())
        ).ask()
    )


@handle_questionary_abort
def _set_doc_types() -> list[FileSuffix]:
    choices = [
        Choice(title=suffix, value=suffix, checked=suffix in DEFAULT_DOC_SUFFIX)
        for suffix in sorted(DOC_SUFFIX)
    ]

    return set(questionary.checkbox(message="Select doc file types.", choices=choices).ask())


@handle_questionary_abort
def _set_provider() -> Provider:
    return questionary.select(
        message="Which LLM provider?",
        choices=[Choice(title=provider.value, value=provider) for provider in Provider],
    ).ask()


@handle_questionary_abort
def _set_exclude_folders(doc_root: Path) -> list[str]:
    doc_root = Path(doc_root)

    def _check_folder(file: Path):
        if file.name.startswith("."):
            return True
        if file.name in EXCLUDE_DIRS:
            return True
        return False

    choices = [
        Choice(title=file.name, value=file.name, checked=_check_folder(file))
        for file in doc_root.iterdir()
        if file.is_dir()
    ]
    if choices:
        return set(
            questionary.checkbox("Select folders to exclude from doc scan", choices=choices).ask()
        )
    return []


@handle_questionary_abort
def _set_default_branch(repo_path: str):
    repo = Repo(str(repo_path), search_parent_directories=True)
    branches = [str(branch) for branch in repo.branches]
    return questionary.select("Select default branch", choices=branches, default="main").ask()


@handle_questionary_abort
def _set_code_repo_root():
    suggested_root = Repo(".", search_parent_directories=True)
    return Path(
        questionary.path(
            "Set path to code root folder",
            only_directories=True,
            default=str(Path(suggested_root.working_dir).resolve()),
        ).ask()
    )


def _validate_url(text):
    try:
        # Will raise if not a valid URL
        HttpUrl(url=text)
        return True
    except ValidationError as e:
        # Extract the first error message
        msg = e.errors()[0]["msg"]
        return f"🚫 {msg}"


@handle_questionary_abort
def _set_deployment_endpoint():
    return questionary.text(message="Azure deployment URL:", validate=_validate_url).ask()


@handle_questionary_abort
def _set_token():
    return SecretStr(questionary.password("Input API token").ask())


@handle_questionary_abort
def _set_state_directory():
    cache_dir = Path(".") / Path(".dope")
    return Path(questionary.path("Set state directory path", default=str(cache_dir.resolve())).ask())


@handle_questionary_abort
def _add_cache_dir_to_git():
    return questionary.confirm("Add cache dir to git?").ask()


def _verify_provider(provider: Provider, base_url: str | None) -> bool:
    if provider == Provider.AZURE:
        if not base_url:
            raise typer.BadParameter(
                f"Missing base URL when provider is set to '{Provider.AZURE.value}'"
            )
        try:
            base_url = HttpUrl(base_url)
        except ValidationError as err:
            raise typer.BadParameter(f"{base_url} not valid URL") from err
    return True


def _create_default_settings(provider: Provider, base_url: str | None, token: SecretStr) -> Settings:
    """Create settings with smart defaults."""
    # Try to detect git repo
    try:
        repo = Repo(".", search_parent_directories=True)
        repo_root = Path(repo.working_tree_dir)
        default_branch = str(repo.active_branch) if repo.active_branch else "main"
    except (InvalidGitRepositoryError, TypeError):
        repo_root = Path.cwd()
        default_branch = "main"

    new_settings = Settings(
        state_directory=Path(".dope"),
        docs=DocSettings(
            docs_root=repo_root,
            doc_filetypes=DEFAULT_DOC_SUFFIX,  # Just .md and .mdx
            exclude_dirs=EXCLUDE_DIRS,
        ),
        git=CodeRepoSettings(
            code_repo_root=repo_root,
            default_branch=default_branch,
        ),
        agent=AgentSettings(
            provider=provider,
            base_url=base_url,
            token=token,
        ),
    )

    return new_settings


def _interactive_setup():
    """Full interactive setup with all options."""
    new_settings = Settings()
    new_settings.state_directory = _set_state_directory()
    add_cache_to_git = _add_cache_dir_to_git()
    new_settings.git.code_repo_root = _set_code_repo_root()
    new_settings.git.default_branch = _set_default_branch(new_settings.git.code_repo_root)
    new_settings.docs.docs_root = Path(_set_doc_root())
    new_settings.docs.exclude_dirs = _set_exclude_folders(new_settings.docs.docs_root)
    new_settings.docs.doc_filetypes = _set_doc_types()
    new_settings.agent.provider = _set_provider()
    if new_settings.agent.provider == Provider.AZURE:
        new_settings.agent.base_url = _set_deployment_endpoint()
    else:
        new_settings.agent.base_url = None
    new_settings.agent.token = _set_token()

    return new_settings, add_cache_to_git


@app.command()
def show(
    format: Annotated[
        str, typer.Option(help="Output format: table (default), json, yaml")
    ] = "table",
):
    """Display current configuration."""
    settings = require_config()

    if format == "json":
        import json

        # Exclude sensitive fields
        safe_dump = settings.model_dump(mode="json", exclude={"agent": {"token"}})
        console.print_json(json.dumps(safe_dump, indent=2))

    elif format == "yaml":
        import yaml

        safe_dump = settings.model_dump(mode="json", exclude={"agent": {"token"}})
        console.print(yaml.dump(safe_dump, sort_keys=False))

    else:  # table (default)
        table = Table(title="DOPE Configuration", show_header=True, header_style="bold cyan")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        # General settings
        table.add_row("State Directory", str(settings.state_directory))
        table.add_row("", "")  # Spacer

        # Git settings
        table.add_row("[bold]Git Settings[/bold]", "")
        table.add_row("  Code Root", str(settings.git.code_repo_root))
        table.add_row("  Default Branch", settings.git.default_branch)
        table.add_row("", "")

        # Docs settings
        table.add_row("[bold]Docs Settings[/bold]", "")
        table.add_row("  Docs Root", str(settings.docs.docs_root))
        table.add_row("  File Types", ", ".join(sorted(settings.docs.doc_filetypes)))
        exclude_list = sorted(list(settings.docs.exclude_dirs))
        exclude_display = (
            ", ".join(exclude_list[:5]) + (", ..." if len(exclude_list) > 5 else "")
        )
        table.add_row("  Excluded Dirs", exclude_display)
        table.add_row("", "")

        # Agent settings
        table.add_row("[bold]LLM Settings[/bold]", "")
        table.add_row("  Provider", settings.agent.provider.value)
        if settings.agent.base_url:
            table.add_row("  Base URL", str(settings.agent.base_url))
        table.add_row("  Token", "[dim]●●●●●●●●[/dim] (hidden)")

        console.print(table)

        # Show config file location
        from app import config_filepath

        console.print(f"\n📄 Config file: [blue]{config_filepath}[/blue]")


@app.command()
def init(
    interactive: Annotated[
        bool, typer.Option("--interactive", "-i", help="Full interactive setup")
    ] = False,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing config")] = False,
    provider: Annotated[
        Provider, typer.Option(help="Choose LLM provider to use")
    ] = Provider.OPENAI,
    base_url: Annotated[
        str | None, typer.Option("--base-url", help="Deployment base URL for Azure")
    ] = None,
):
    """Initialize configuration (quickstart by default, --interactive for full setup)."""
    _verify_provider(provider=provider, base_url=base_url)

    local_config_path = locate_local_config_file(CONFIG_FILENAME)

    if local_config_path and not force:
        rprint(f"[yellow]⚠️  Config already exists at {local_config_path}[/yellow]")
        if typer.confirm("Overwrite?"):
            force = True
        else:
            rprint("[blue]Keeping existing config[/blue]")
            raise typer.Exit()

    add_cache_to_git = False

    if not interactive:
        # QUICKSTART MODE - minimal questions
        rprint("[bold cyan]🚀 Quick setup[/bold cyan] (use --interactive for full configuration)")
        rprint("")

        # Only ask essential questions
        provider = _set_provider()

        if provider == Provider.AZURE:
            base_url = _set_deployment_endpoint()
        else:
            base_url = None

        token = _set_token()

        # Use smart defaults for everything else
        new_settings = _create_default_settings(provider, base_url, token)

        rprint("\n[green]✅ Config created with defaults:[/green]")
        rprint(f"  📁 Docs root: [blue]{new_settings.docs.docs_root}[/blue]")
        rprint(f"  🔧 Code root: [blue]{new_settings.git.code_repo_root}[/blue]")
        rprint(f"  💾 State dir: [blue]{new_settings.state_directory}[/blue]")
        rprint(f"  🌿 Default branch: [blue]{new_settings.git.default_branch}[/blue]")
        rprint("\n[dim]💡 Run 'dope config show' to see all settings[/dim]")
        rprint("[dim]💡 Run 'dope config init -i --force' for full customization[/dim]")

    else:
        # INTERACTIVE MODE - all questions
        rprint("[bold cyan]🔧 Interactive setup[/bold cyan]")
        rprint("")
        new_settings, add_cache_to_git = _interactive_setup()

    # Save config
    cache_dir = generate_local_cache(new_settings.state_directory, add_to_git=add_cache_to_git)
    generate_local_config_file(CONFIG_FILENAME, new_settings)

    rprint(f"\n[green]✅ Configuration saved to {Path.cwd() / CONFIG_FILENAME}[/green]")


@app.command()
def validate():
    """Validate current configuration."""
    settings = require_config()

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
    if not settings.agent.token:
        errors.append("LLM token not configured")

    if settings.agent.provider == Provider.AZURE and not settings.agent.base_url:
        errors.append("Azure provider requires base_url to be set")

    # Display results
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
        return

    if errors:
        console.print("\n[blue]💡 Run 'dope config init --force' to fix[/blue]")
        raise typer.Exit(1)


@app.command()
def set(
    key: Annotated[str, typer.Argument(help="Setting key (e.g., 'git.default_branch')")],
    value: Annotated[str, typer.Argument(help="New value")],
):
    """Update a single configuration value."""
    settings = require_config()

    # Parse nested key
    parts = key.split(".")

    try:
        # Navigate to the setting
        obj = settings
        for part in parts[:-1]:
            obj = getattr(obj, part)

        # Get the field name and current value
        field_name = parts[-1]
        old_value = getattr(obj, field_name)

        # Set new value (with type conversion)
        if isinstance(old_value, bool):
            new_value = value.lower() in ("true", "1", "yes")
        elif isinstance(old_value, Path):
            new_value = Path(value)
        elif isinstance(old_value, set):
            new_value = set(value.split(","))
        else:
            new_value = type(old_value)(value)

        setattr(obj, field_name, new_value)

        # Save config
        from app import config_filepath

        generate_local_config_file(CONFIG_FILENAME, settings)

        rprint(f"[green]✅ Updated {key}:[/green] {old_value} → {new_value}")
        rprint(f"[dim]📄 Saved to {config_filepath}[/dim]")

    except AttributeError:
        rprint(f"[red]❌ Unknown setting: {key}[/red]")
        rprint("[blue]💡 Run 'dope config show' to see available settings[/blue]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
