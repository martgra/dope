"""Suggester service for generating documentation change suggestions.

This service orchestrates the generation of documentation update suggestions
based on code and documentation changes.
"""

from typing import Any, Protocol

from dope.core.protocols import UsageTrackerProtocol
from dope.core.usage import UsageTracker
from dope.models.domain.documentation import DocSuggestions
from dope.models.domain.scope import ScopeTemplate
from dope.models.settings import ScopeFilterSettings
from dope.repositories import SuggestionRepository
from dope.services.suggester.change_processor import ChangeProcessor
from dope.services.suggester.prompts import SUGGESTION_PROMPT
from dope.services.suggester.scope_filter import ScopeAlignmentFilter


class SuggestionAgent(Protocol):
    """Protocol for suggestion generation agents."""

    def run_sync(self, *, _user_prompt: str, usage: Any) -> Any:
        """Run the agent synchronously.

        Args:
            user_prompt: Prompt for the agent
            usage: Usage tracking object

        Returns:
            Agent result with .output attribute
        """
        ...


class DocChangeSuggester:
    """Generates documentation change suggestions based on code and doc changes.

    Uses dependency injection for testability and decoupling from
    specific agent implementations.

    Args:
        repository: Repository for suggestion state persistence
        scope: Project documentation scope template (optional)
        scope_filter_settings: Settings for scope-based filtering (optional)
        agent: Agent for generating suggestions (optional, lazy-loaded)
        usage_tracker: Tracker for LLM usage statistics

    Example:
        >>> repo = SuggestionRepository(Path(".dope/suggestions.json"))
        >>> scope = load_scope()
        >>> suggester = DocChangeSuggester(repository=repo, scope=scope)
        >>> suggestions = suggester.get_suggestions(
        ...     docs_change=doc_state,
        ...     code_change=code_state,
        ... )
    """

    def __init__(
        self,
        *,
        repository: SuggestionRepository,
        scope: ScopeTemplate | None = None,
        scope_filter_settings: ScopeFilterSettings | None = None,
        agent: SuggestionAgent | None = None,
        usage_tracker: UsageTrackerProtocol | None = None,
    ):
        """Initialize suggester with dependencies.

        Args:
            repository: Repository for state persistence
            scope: Optional project scope for filtering
            scope_filter_settings: Optional filter settings
            agent: Optional pre-configured agent (lazy-loaded if not provided)
            usage_tracker: Optional usage tracker
        """
        self._repository = repository
        self._scope = scope
        self._agent = agent
        self._usage_tracker = usage_tracker or UsageTracker()

        # Create scope filter if scope provided
        self._scope_filter = ScopeAlignmentFilter(scope, scope_filter_settings) if scope else None

    @property
    def agent(self) -> SuggestionAgent:
        """Get the suggestion agent, lazy-loading if needed."""
        if self._agent is None:
            from dope.services.suggester.suggester_agents import get_suggester_agent

            self._agent = get_suggester_agent()
        return self._agent

    @property
    def usage_tracker(self) -> UsageTrackerProtocol:
        """Get the usage tracker."""
        return self._usage_tracker

    def get_state(self) -> DocSuggestions:
        """Return the current suggestion state.

        Returns:
            DocSuggestions from stored state
        """
        return self._repository.get_suggestions()

    def get_suggestions(
        self,
        *,
        docs_change: dict[str, Any],
        code_change: dict[str, Any],
    ) -> DocSuggestions:
        """Generate documentation update suggestions.

        Filters out skipped files, applies scope-based filtering if scope available,
        prioritizes HIGH priority changes, and includes change magnitude metadata.

        Args:
            docs_change: Dictionary of documentation changes with state
            code_change: Dictionary of code changes with metadata

        Returns:
            DocSuggestions with prioritized and filtered suggestions
        """
        # Filter to processable files only
        processable_code = ChangeProcessor.filter_processable_files(code_change)
        processable_docs = ChangeProcessor.filter_processable_files(docs_change)

        # Apply scope-based filtering if scope available
        if self._scope_filter:
            processable_code, _relevance_map = self._scope_filter.filter_changes(processable_code)

        # Early return if no processable changes
        if not processable_code:
            return DocSuggestions(changes_to_apply=[])

        # Check cache validity
        state_hash = self._repository.get_state_hash(
            code_change=processable_code,
            docs_change=processable_docs,
        )

        if self._repository.is_state_valid(state_hash):
            return self._repository.get_suggestions()

        # Build prompt with metadata
        prompt = self._build_prompt(
            processable_docs=processable_docs,
            processable_code=processable_code,
        )

        # Generate suggestions
        result = self.agent.run_sync(
            user_prompt=prompt,
            usage=self._usage_tracker.usage,
        )
        suggestions = result.output

        # Save and return
        self._repository.save_suggestions(suggestions, state_hash)

        return suggestions

    def _build_prompt(
        self,
        *,
        processable_docs: dict[str, Any],
        processable_code: dict[str, Any],
    ) -> str:
        """Build the suggestion prompt.

        Args:
            processable_docs: Filtered documentation changes
            processable_code: Filtered code changes (with scope alignment if available)

        Returns:
            Formatted prompt string
        """
        return SUGGESTION_PROMPT.format(
            documentation=ChangeProcessor.format_changes_for_prompt(
                processable_docs,
                include_metadata=False,
            ),
            code_changes=ChangeProcessor.format_changes_for_prompt(
                processable_code,
                include_metadata=True,
            ),
        )


# Backward compatibility - factory function for old interface
def create_suggester(
    suggestion_state_path: Any,
    usage_tracker: UsageTrackerProtocol | None = None,
) -> DocChangeSuggester:
    """Factory function for backward compatibility.

    Args:
        suggestion_state_path: Path to suggestion state file
        usage_tracker: Optional usage tracker

    Returns:
        Configured DocChangeSuggester instance
    """
    from pathlib import Path

    repository = SuggestionRepository(Path(suggestion_state_path))
    return DocChangeSuggester(
        repository=repository,
        usage_tracker=usage_tracker,
    )
