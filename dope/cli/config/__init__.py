"""Configuration management commands."""

from pathlib import Path
from typing import Annotated

import typer
from pydantic import HttpUrl, ValidationError
from rich import print as rprint

from dope.cli.config.defaults import create_default_settings
from dope.cli.config.display import (
    display_config_json,
    display_config_table,
    display_config_yaml,
)
from dope.cli.config.interactive import (
    prompt_add_cache_to_git,
    prompt_code_repo_root,
    prompt_default_branch,
    prompt_deployment_endpoint,
    prompt_doc_root,
    prompt_doc_types,
    prompt_exclude_folders,
    prompt_provider,
    prompt_state_directory,
    prompt_token,
)
from dope.cli.config.validation import display_validation_results, validate_config
from dope.core.config_io import generate_local_cache, generate_local_config_file
from dope.core.config_locator import locate_local_config_file
from dope.core.utils import require_config
from dope.models.constants import CONFIG_FILENAME
from dope.models.enums import Provider
from dope.models.settings import AgentSettings, Settings

app = typer.Typer(help="Manage application configuration")


def verify_provider(provider: Provider, base_url: str | None) -> bool:
    """Verify provider configuration is valid."""
    if provider == Provider.AZURE:
        if not base_url:
            raise typer.BadParameter(
                f"Missing base URL when provider is set to '{Provider.AZURE.value}'"
            )
        try:
            HttpUrl(base_url)
        except ValidationError as err:
            raise typer.BadParameter(f"{base_url} not valid URL") from err
    return True


def interactive_setup() -> tuple[Settings, bool]:
    """Run full interactive setup with all options.

    Returns:
        Tuple of (settings, add_cache_to_git)
    """
    new_settings = Settings()
    new_settings.state_directory = prompt_state_directory()
    add_cache_to_git = prompt_add_cache_to_git()
    new_settings.git.code_repo_root = prompt_code_repo_root()
    new_settings.git.default_branch = prompt_default_branch(new_settings.git.code_repo_root)
    new_settings.docs.docs_root = prompt_doc_root()
    new_settings.docs.exclude_dirs = prompt_exclude_folders(new_settings.docs.docs_root)
    new_settings.docs.doc_filetypes = prompt_doc_types()
    provider = prompt_provider()
    base_url = prompt_deployment_endpoint() if provider == Provider.AZURE else None
    token = prompt_token()
    new_settings.agent = AgentSettings(
        provider=provider,
        base_url=base_url,
        token=token,
    )

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
        display_config_json(settings)
    elif format == "yaml":
        display_config_yaml(settings)
    else:  # table (default)
        display_config_table(settings)


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
    verify_provider(provider=provider, base_url=base_url)

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
        provider = prompt_provider()
        base_url = prompt_deployment_endpoint() if provider == Provider.AZURE else None
        token = prompt_token()

        # Use smart defaults for everything else
        new_settings = create_default_settings(provider, base_url, token)

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
        new_settings, add_cache_to_git = interactive_setup()

    # Save config
    generate_local_cache(new_settings.state_directory, add_to_git=add_cache_to_git)
    generate_local_config_file(CONFIG_FILENAME, new_settings)

    rprint(f"\n[green]✅ Configuration saved to {Path.cwd() / CONFIG_FILENAME}[/green]")


@app.command()
def validate():
    """Validate current configuration."""
    settings = require_config()
    errors, warnings = validate_config(settings)
    is_valid = display_validation_results(errors, warnings)

    if not is_valid:
        raise typer.Exit(1)


@app.command(name="set")
def update_setting(
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
        from dope import config_filepath

        generate_local_config_file(CONFIG_FILENAME, settings)

        rprint(f"[green]✅ Updated {key}:[/green] {old_value} → {new_value}")
        rprint(f"[dim]📄 Saved to {config_filepath}[/dim]")

    except AttributeError as e:
        rprint(f"[red]❌ Unknown setting: {key}[/red]")
        rprint("[blue]💡 Run 'dope config show' to see available settings[/blue]")
        raise typer.Exit(1) from e
    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1) from e
