"""Display formatters for configuration, status, and other CLI outputs."""

import json
from pathlib import Path

import yaml
from rich.table import Table

from dope.cli.ui.console import console
from dope.models.settings import Settings


class ConfigFormatter:
    """Format and display configuration information."""

    @staticmethod
    def display_table(settings: Settings) -> None:
        """Display configuration as formatted table.

        Args:
            settings: Application settings to display
        """
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

    @staticmethod
    def display_json(settings: Settings) -> None:
        """Display configuration as JSON.

        Args:
            settings: Application settings to display
        """
        safe_dump = settings.model_dump(mode="json", exclude={"agent": {"token"}})
        console.print_json(json.dumps(safe_dump, indent=2))

    @staticmethod
    def display_yaml(settings: Settings) -> None:
        """Display configuration as YAML.

        Args:
            settings: Application settings to display
        """
        safe_dump = settings.model_dump(mode="json", exclude={"agent": {"token"}})
        console.print(yaml.dump(safe_dump, sort_keys=False))


class StatusFormatter:
    """Format and display project status information."""

    @staticmethod
    def display_status(
        docs_scanned: int,
        docs_summarized: int,
        code_scanned: int,
        code_summarized: int,
        suggestions_count: int,
        scope_exists: bool,
        state_directory: Path,
    ) -> None:
        """Display comprehensive status table with next steps.

        Args:
            docs_scanned: Number of documentation files scanned
            docs_summarized: Number of documentation files with summaries
            code_scanned: Number of code files scanned
            code_summarized: Number of code files with summaries
            suggestions_count: Number of pending suggestions
            scope_exists: Whether scope configuration exists
            state_directory: Path to state directory
        """
        # Create status table
        table = Table(title="DOPE Status", show_header=True, header_style="bold cyan")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")

        # Documentation status
        if docs_scanned > 0:
            table.add_row(
                "Documentation Files",
                f"{docs_summarized}/{docs_scanned} scanned and summarized",
            )
        else:
            table.add_row("Documentation Files", "[dim]Not scanned yet[/dim]")

        # Code status
        if code_scanned > 0:
            table.add_row("Code Files", f"{code_summarized}/{code_scanned} scanned and summarized")
        else:
            table.add_row("Code Files", "[dim]Not scanned yet[/dim]")

        # Suggestions status
        if suggestions_count > 0:
            table.add_row("Suggestions", f"{suggestions_count} ready to apply")
        else:
            table.add_row("Suggestions", "[dim]No suggestions generated[/dim]")

        # Scope status
        if scope_exists:
            table.add_row("Documentation Scope", "✓ Configured")
        else:
            table.add_row("Documentation Scope", "[dim]Not configured[/dim]")

        console.print(table)

        # Show next steps
        console.print("\n[bold cyan]Next Steps:[/bold cyan]")
        if docs_scanned == 0 and code_scanned == 0:
            console.print("  • Run [blue]dope update[/blue] to scan and update everything")
            console.print("    or use individual commands:")
        if docs_scanned == 0:
            console.print("  1. Run [blue]dope scan docs[/blue] to scan documentation")
        if code_scanned == 0:
            console.print("  2. Run [blue]dope scan code[/blue] to scan code changes")
        if suggestions_count == 0 and (docs_scanned > 0 or code_scanned > 0):
            console.print("  3. Run [blue]dope suggest[/blue] to generate suggestions")
        if suggestions_count > 0:
            console.print("  4. Run [blue]dope apply[/blue] to apply suggestions")

        # Show state directory
        console.print(f"\n📁 State directory: [blue]{state_directory}[/blue]")

    @staticmethod
    def display_dry_run_preview(changes: list) -> None:
        """Display dry-run preview of changes.

        Args:
            changes: List of change objects with documentation_file_path and suggested_changes
        """
        console.print("\n[yellow]Dry run - showing suggestions without applying:[/yellow]")
        for change in changes:
            console.print(f"  • {change.documentation_file_path} ({change.change_type})")
            if change.suggested_changes:
                for suggestion in change.suggested_changes[:2]:  # Show first 2
                    text = suggestion.suggestion
                    preview = text[:80] if len(text) > 80 else text
                    console.print(f"    - {preview}...")
        console.print(f"\n[yellow]Total changes: {len(changes)}[/yellow]")
        console.print("[yellow]Run without --dry-run to apply changes[/yellow]")
