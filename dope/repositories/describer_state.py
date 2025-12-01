"""Describer-specific state repository implementation."""

from pathlib import Path
from typing import Any

from dope.repositories.json_state import JsonStateRepository


class DescriberRepository(JsonStateRepository):
    """Repository for managing file description state.

    Extends JsonStateRepository with describer-specific operations,
    handling file hashes and summaries for change detection.

    Args:
        state_path: Path to the describer state JSON file.

    Example:
        >>> repo = DescriberRepository(Path(".dope/doc-state.json"))
        >>> state = repo.load()
        >>> if repo.is_file_changed("README.md", new_hash):
        ...     # File needs re-describing
    """

    def __init__(self, state_path: Path):
        """Initialize repository with state file path.

        Args:
            state_path: Path where describer state will be persisted.
        """
        super().__init__(state_path)

    def get_file_state(self, file_path: str) -> dict[str, Any] | None:
        """Get state for a specific file.

        Args:
            file_path: Path to the file (as string key).

        Returns:
            File state dictionary, or None if not found.
        """
        state = self.load()
        return state.get(file_path)

    def is_file_changed(self, file_path: str, current_hash: str) -> bool:
        """Check if a file has changed based on hash comparison.

        Args:
            file_path: Path to the file (as string key).
            current_hash: Current hash of the file content.

        Returns:
            True if file is new or hash has changed, False if unchanged.
        """
        file_state = self.get_file_state(file_path)
        if file_state is None:
            return True
        return file_state.get("hash") != current_hash

    def needs_summary(self, file_path: str) -> bool:
        """Check if a file needs its summary generated.

        Args:
            file_path: Path to the file (as string key).

        Returns:
            True if summary is missing or None, False otherwise.
        """
        file_state = self.get_file_state(file_path)
        if file_state is None:
            return True
        if file_state.get("skipped"):
            return False
        return file_state.get("summary") is None

    def update_file_state(
        self,
        file_path: str,
        *,
        file_hash: str | None = None,
        summary: dict[str, Any] | None = None,
        priority: str | None = None,
        metadata: dict[str, Any] | None = None,
        skipped: bool = False,
        skip_reason: str | None = None,
    ) -> None:
        """Update state for a specific file.

        Args:
            file_path: Path to the file (as string key).
            file_hash: Hash of file content (None to keep existing).
            summary: Generated summary (None to keep existing).
            priority: Priority classification (None to keep existing).
            metadata: Additional metadata (None to keep existing).
            skipped: Whether file was skipped.
            skip_reason: Reason for skipping.
        """
        state = self.load()

        if file_path not in state:
            state[file_path] = {}

        if skipped:
            state[file_path] = {
                "hash": None,
                "skipped": True,
                "skip_reason": skip_reason,
                "metadata": metadata or {},
            }
        else:
            if file_hash is not None:
                state[file_path]["hash"] = file_hash
            if summary is not None:
                state[file_path]["summary"] = summary
            if priority is not None:
                state[file_path]["priority"] = priority
            if metadata is not None:
                state[file_path]["metadata"] = metadata

        self.save(state)

    def remove_stale_files(self, current_files: set[str]) -> list[str]:
        """Remove files from state that no longer exist.

        Args:
            current_files: Set of currently discovered file paths.

        Returns:
            List of file paths that were removed from state.
        """
        state = self.load()
        removed = []

        for file_path in list(state.keys()):
            if file_path not in current_files:
                del state[file_path]
                removed.append(file_path)

        if removed:
            self.save(state)

        return removed

    def get_files_needing_summary(self) -> list[str]:
        """Get list of files that need summaries generated.

        Returns:
            List of file paths that need summaries.
        """
        state = self.load()
        return [
            file_path
            for file_path, file_state in state.items()
            if not file_state.get("skipped") and file_state.get("summary") is None
        ]

    def get_processable_files(self) -> dict[str, Any]:
        """Get files that are not skipped and have summaries.

        Returns:
            Dictionary of processable files with their state.
        """
        state = self.load()
        return {
            file_path: file_state
            for file_path, file_state in state.items()
            if not file_state.get("skipped") and file_state.get("summary") is not None
        }
