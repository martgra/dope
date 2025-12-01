from abc import ABC, abstractmethod
from pathlib import Path


class BaseConsumer(ABC):
    """Base consumer class for file discovery and content access.

    Subclasses must call super().__init__() or set root_path themselves.
    """

    root_path: Path

    def __init__(self, root_path: str | Path) -> None:
        """Initialize the consumer with a root path.

        Args:
            root_path: Root directory for file operations.
        """
        self.root_path = Path(root_path)

    @abstractmethod
    def discover_files(self) -> list[Path]:
        """Discover files."""
        pass

    @abstractmethod
    def get_content(self, file_path: Path) -> bytes:
        """Get file content."""
        pass

    def get_structure(self, paths: list[Path]) -> str:
        """Return tree structure of paths.

        Args:
            paths: List of file paths to visualize

        Returns:
            String representation of directory tree
        """
        from dope.core.tree import get_structure

        return get_structure(paths, base_dir=Path("."))
