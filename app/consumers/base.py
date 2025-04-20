from abc import ABC, abstractmethod
from pathlib import Path


class BaseConsumer(ABC):
    """Base consumer clas."""

    @abstractmethod
    def __init__(self, root_path: str | Path):
        pass

    @abstractmethod
    def discover_files(self) -> list[Path]:
        """Discover files."""
        pass

    @abstractmethod
    def get_content(self, file_path) -> bytes:
        """Get file content."""
        pass
