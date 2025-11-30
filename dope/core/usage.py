"""Usage tracking for LLM token consumption."""

from dataclasses import dataclass, field

from pydantic_ai.usage import Usage


@dataclass
class UsageTracker:
    """Track LLM usage for a command execution.

    Replaces the singleton UsageContext pattern with explicit dependency injection.
    Each command creates its own tracker and passes it to services.
    """

    usage: Usage = field(default_factory=Usage)

    def log(self) -> None:
        """Log current usage statistics to console."""
        print(f"Total tokens used: {self.usage.total_tokens or 0}")

    def get_total_tokens(self) -> int:
        """Get total token count.

        Returns:
            Total number of tokens used
        """
        return self.usage.total_tokens or 0

    def get_details(self) -> dict:
        """Get detailed usage information.

        Returns:
            Dictionary with usage details
        """
        return {
            "total_tokens": self.usage.total_tokens or 0,
            "request_tokens": self.usage.request_tokens or 0,
            "response_tokens": self.usage.response_tokens or 0,
            "total_cost": self.usage.total_cost or 0.0,
        }
