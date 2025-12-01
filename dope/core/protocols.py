"""Protocol definitions for dependency injection and testability.

These protocols define the contracts between layers, enabling:
- Easy mocking in unit tests
- Swappable implementations
- Clear separation of concerns

Note: Prefer using concrete classes with duck typing over protocols
when there's only one implementation. Protocols are most useful when
multiple implementations are expected.
"""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StateRepository(Protocol):
    """Protocol for state persistence operations.

    Implementations handle loading, saving, and caching of application state.
    This abstraction allows for different storage backends (JSON, YAML, database).

    Used by: JsonStateRepository
    """

    def load(self) -> dict[str, Any]:
        """Load state from storage.

        Returns:
            Dictionary containing the stored state, or empty dict if not found.
        """
        ...

    def save(self, state: dict[str, Any]) -> None:
        """Save state to storage.

        Args:
            state: Dictionary containing the state to persist.
        """
        ...


@runtime_checkable
class FileConsumer(Protocol):
    """Protocol for file discovery and content access.

    Implementations provide file system or VCS-aware file operations.

    Used by: GitConsumer, DocConsumer
    """

    root_path: Path

    def discover_files(self) -> list[Path]:
        """Discover files according to implementation-specific rules.

        Returns:
            List of paths to discovered files.
        """
        ...

    def get_content(self, file_path: Path) -> bytes:
        """Read content of a file.

        Args:
            file_path: Path to the file to read.

        Returns:
            File content as bytes.
        """
        ...


@runtime_checkable
class UsageTrackerProtocol(Protocol):
    """Protocol for tracking LLM usage and costs.

    Used by: UsageTracker, DocChangeSuggester
    """

    def log(self) -> None:
        """Log current usage statistics."""
        ...

    @property
    def usage(self) -> Any:
        """Get usage data for passing to agents."""
        ...
