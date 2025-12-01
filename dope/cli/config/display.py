"""Configuration display and formatting functions."""

import json

import yaml
from rich.console import Console
from rich.table import Table

from dope.models.settings import Settings

console = Console()


def display_config_table(settings: Settings) -> None:
    """Display configuration as formatted table."""
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
    exclude_display = ", ".join(exclude_list[:5]) + (", ..." if len(exclude_list) > 5 else "")
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
    from dope import config_filepath

    console.print(f"\n📄 Config file: [blue]{config_filepath}[/blue]")


def display_config_json(settings: Settings) -> None:
    """Display configuration as JSON."""
    safe_dump = settings.model_dump(mode="json", exclude={"agent": {"token"}})
    console.print_json(json.dumps(safe_dump, indent=2))


def display_config_yaml(settings: Settings) -> None:
    """Display configuration as YAML."""
    safe_dump = settings.model_dump(mode="json", exclude={"agent": {"token"}})
    console.print(yaml.dump(safe_dump, sort_keys=False))
