"""Usage tracking for LLM token consumption."""

from dataclasses import dataclass, field

from pydantic_ai.usage import Usage
from rich.console import Console

console = Console(stderr=True)


@dataclass
class UsageTracker:
    """Track LLM usage for a command execution.

    Replaces the singleton UsageContext pattern with explicit dependency injection.
    Each command creates its own tracker and passes it to services.
    """

    usage: Usage = field(default_factory=Usage)

    def log(self) -> None:
        """Log current usage statistics to stderr."""
        total = self.usage.total_tokens or 0
        console.print(f"[dim]Total tokens used: {total}[/dim]")
