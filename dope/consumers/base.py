from abc import ABC, abstractmethod
from pathlib import Path


class BaseConsumer(ABC):
    """Base consumer class."""

    @abstractmethod
    def __init__(self, root_path: str | Path):
        self.root_path = root_path

    @abstractmethod
    def discover_files(self) -> list[Path]:
        """Discover files."""
        pass

    @abstractmethod
    def get_content(self, file_path) -> bytes:
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
