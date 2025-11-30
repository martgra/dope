"""Abstract state management for persistence."""

import hashlib
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


class StateManager[T](ABC):
    """Abstract base class for state persistence.

    Provides common interface for loading, saving, and hashing state data.
    Subclasses implement serialization/deserialization logic.
    """

    def __init__(self, state_path: Path):
        """Initialize state manager.

        Args:
            state_path: Path where state will be persisted
        """
        self.state_path = Path(state_path)

    @abstractmethod
    def serialize(self, data: T) -> str:
        """Serialize state data to string.

        Args:
            data: State data to serialize

        Returns:
            String representation of state
        """
        pass

    @abstractmethod
    def deserialize(self, content: str) -> T:
        """Deserialize string to state data.

        Args:
            content: String content to deserialize

        Returns:
            Deserialized state data
        """
        pass

    def save(self, state: T) -> None:
        """Save state to disk.

        Args:
            state: State data to save
        """
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.serialize(state)
        self.state_path.write_text(content, encoding="utf-8")

    def load(self) -> T | None:
        """Load state from disk.

        Returns:
            Loaded state data, or None if file doesn't exist
        """
        if not self.state_path.exists():
            return None
        content = self.state_path.read_text(encoding="utf-8")
        return self.deserialize(content)

    def exists(self) -> bool:
        """Check if state file exists.

        Returns:
            True if state file exists
        """
        return self.state_path.exists()

    def compute_hash(self, state: T) -> str:
        """Compute MD5 hash of state for caching/comparison.

        Args:
            state: State data to hash

        Returns:
            MD5 hash of serialized state
        """
        content = self.serialize(state)
        return hashlib.md5(content.encode()).hexdigest()


class JsonStateManager(StateManager[dict]):
    """JSON-based state persistence."""

    def serialize(self, data: dict) -> str:
        """Serialize dict to formatted JSON string."""
        return json.dumps(data, ensure_ascii=False, indent=2)

    def deserialize(self, content: str) -> dict:
        """Deserialize JSON string to dict."""
        return json.loads(content)
