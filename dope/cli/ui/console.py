"""Unified console output and messaging."""

from rich.console import Console

# Singleton console instance
console = Console()


def info(message: str) -> None:
    """Display informational message.

    Args:
        message: Message to display
    """
    console.print(f"[cyan]→ {message}[/cyan]")


def success(message: str) -> None:
    """Display success message.

    Args:
        message: Message to display
    """
    console.print(f"[green]✓ {message}[/green]")


def warning(message: str) -> None:
    """Display warning message.

    Args:
        message: Message to display
    """
    console.print(f"[yellow]⚠ {message}[/yellow]")


def error(message: str) -> None:
    """Display error message.

    Args:
        message: Message to display
    """
    console.print(f"[red]✗ {message}[/red]")
