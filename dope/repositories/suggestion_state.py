"""Suggestion-specific state repository implementation."""

from pathlib import Path
from typing import Any

from dope.models.domain.documentation import DocSuggestions
from dope.repositories.json_state import JsonStateRepository


class SuggestionRepository(JsonStateRepository):
    """Repository for managing documentation suggestion state.

    Extends JsonStateRepository with suggestion-specific operations,
    providing typed access to DocSuggestions model.

    Args:
        state_path: Path to the suggestion state JSON file.

    Example:
        >>> repo = SuggestionRepository(Path(".dope/suggestion-state.json"))
        >>> suggestions = repo.get_suggestions()
        >>> if repo.is_state_valid(current_hash):
        ...     return suggestions  # Use cached
    """

    def __init__(self, state_path: Path):
        """Initialize repository with state file path.

        Args:
            state_path: Path where suggestion state will be persisted.
        """
        super().__init__(state_path)

    def get_suggestions(self) -> DocSuggestions:
        """Get DocSuggestions model from stored state.

        Returns:
            DocSuggestions instance. Returns empty suggestions if
            state doesn't exist or is invalid.
        """
        state = self.load()
        suggestion_data = state.get("suggestion", {})

        # If no suggestion data exists, return empty DocSuggestions
        if not suggestion_data:
            return DocSuggestions(changes_to_apply=[])

        return DocSuggestions.model_validate(suggestion_data)

    def save_suggestions(
        self,
        suggestions: DocSuggestions,
        state_hash: str,
    ) -> None:
        """Save suggestions with associated hash for cache validation.

        Args:
            suggestions: DocSuggestions instance to persist.
            state_hash: Hash of input data for cache invalidation.
        """
        state = {
            "hash": state_hash,
            "suggestion": suggestions.model_dump(),
        }
        self.save(state)

    def is_state_valid(self, current_hash: str) -> bool:
        """Check if cached suggestions are still valid.

        Compares provided hash against stored hash to determine if
        the cached suggestions can be reused.

        Args:
            current_hash: Hash of current input data.

        Returns:
            True if cached state is valid (hashes match), False otherwise.
        """
        return self.is_hash_valid(current_hash)

    def get_state_hash(self, *, docs_change: dict[str, Any], code_change: dict[str, Any]) -> str:
        """Calculate hash for current documentation and code changes.

        This hash is used to determine if suggestions need to be regenerated.

        Args:
            docs_change: Dictionary of documentation changes.
            code_change: Dictionary of code changes.

        Returns:
            MD5 hash of the combined changes.
        """
        return self.compute_hash(docs_change, code_change)
