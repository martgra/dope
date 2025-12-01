"""Generic JSON-based state repository implementation."""

import hashlib
import json
from pathlib import Path
from typing import Any


class JsonStateRepository:
    """Generic JSON state repository for file-based persistence.

    Provides a reusable implementation for loading, saving, and hashing
    state data stored in JSON format. This replaces duplicated persistence
    logic across services.

    Args:
        state_path: Path to the JSON state file.

    Example:
        >>> repo = JsonStateRepository(Path(".dope/state.json"))
        >>> state = repo.load()
        >>> state["new_key"] = "new_value"
        >>> repo.save(state)
    """

    def __init__(self, state_path: Path):
        """Initialize repository with state file path.

        Args:
            state_path: Path where state will be persisted.
        """
        self._path = state_path

    @property
    def path(self) -> Path:
        """Get the state file path."""
        return self._path

    def exists(self) -> bool:
        """Check if state file exists.

        Returns:
            True if state file exists, False otherwise.
        """
        return self._path.is_file()

    def load(self) -> dict[str, Any]:
        """Load state from JSON file.

        Returns:
            Dictionary containing stored state, or empty dict if file
            doesn't exist or is invalid JSON.
        """
        if not self._path.is_file():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self, state: dict[str, Any]) -> None:
        """Save state to JSON file.

        Creates parent directories if they don't exist.

        Args:
            state: Dictionary to persist as JSON.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def compute_hash(self, *args: Any) -> str:
        """Compute MD5 hash from multiple data inputs.

        Useful for cache invalidation by hashing input data and comparing
        against stored hash.

        Args:
            *args: Data to include in hash. Each argument is JSON-serialized.

        Returns:
            MD5 hexdigest of the combined data.

        Example:
            >>> repo = JsonStateRepository(Path("state.json"))
            >>> hash1 = repo.compute_hash({"key": "value"}, [1, 2, 3])
            >>> hash2 = repo.compute_hash({"key": "value"}, [1, 2, 3])
            >>> hash1 == hash2
            True
        """
        combined = b"".join(
            json.dumps(arg, sort_keys=True, default=str).encode("utf-8") for arg in args
        )
        return hashlib.md5(combined).hexdigest()

    def get_stored_hash(self) -> str | None:
        """Get hash value from stored state.

        Returns:
            Stored hash string, or None if not present.
        """
        state = self.load()
        return state.get("hash")

    def is_hash_valid(self, current_hash: str) -> bool:
        """Check if stored hash matches current hash.

        Args:
            current_hash: Hash to compare against stored value.

        Returns:
            True if hashes match, False otherwise.
        """
        return self.get_stored_hash() == current_hash

    def delete(self) -> bool:
        """Delete the state file if it exists.

        Returns:
            True if file was deleted, False if it didn't exist.
        """
        if self._path.is_file():
            self._path.unlink()
            return True
        return False
