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


class SuggestionAgent(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for suggestion generation agents."""

    def run_sync(self, *, _user_prompt: str, usage: Any) -> Any:
        """Run the agent synchronously.

        Args:
            user_prompt: Prompt for the agent
            usage: Usage tracking object

        Returns:
            Agent result with .output attribute
        """


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

    def __init__(  # pylint: disable=too-many-arguments
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
        self._doc_term_index = None

        # Load doc term index if pattern enrichment enabled
        if scope_filter_settings is None or scope_filter_settings.enable_pattern_enrichment:
            from dope.core.doc_terms import DocTermIndex
            from dope.models.settings import get_settings

            settings = get_settings()
            doc_term_index_path = settings.doc_terms_path
            if doc_term_index_path.exists():
                self._doc_term_index = DocTermIndex(doc_term_index_path)
                self._doc_term_index.load()

        # Store settings for adaptive pruning
        self._scope_filter_settings = scope_filter_settings or ScopeFilterSettings()

        # Create scope filter if scope provided
        self._scope_filter = (
            ScopeAlignmentFilter(scope, self._scope_filter_settings, self._doc_term_index)
            if scope
            else None
        )

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

    def get_suggestions(  # pylint: disable=too-many-locals
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
        # Track analytics
        analytics = {
            "initial_code_files": len(code_change),
            "initial_doc_files": len(docs_change),
        }

        # Filter to processable files only
        processable_code = ChangeProcessor.filter_processable_files(code_change)
        processable_docs = ChangeProcessor.filter_processable_files(docs_change)

        analytics["processable_code_files"] = len(processable_code)
        analytics["processable_doc_files"] = len(processable_docs)

        # Apply scope-based filtering if scope available
        if self._scope_filter:
            processable_code, _relevance_map = self._scope_filter.filter_changes(processable_code)
            analytics["scope_filtered_code_files"] = len(processable_code)

        # Apply doc term filtering if index available
        if self._doc_term_index:
            processable_docs = self._doc_term_index.filter_relevant_docs(
                code_changes=processable_code,
                doc_state=processable_docs,
                min_match_threshold=self._scope_filter_settings.doc_term_match_threshold,
            )
            analytics["term_filtered_doc_files"] = len(processable_docs)

        # Apply minimum docs threshold (safety net)
        if len(processable_docs) < self._scope_filter_settings.min_docs_threshold:
            # Restore top N docs by priority if we filtered too aggressively
            all_processable = ChangeProcessor.filter_processable_files(docs_change)
            sorted_docs = ChangeProcessor.sort_by_priority(all_processable)

            # Take top N that aren't already included
            current_paths = set(processable_docs.keys())
            for filepath, data in sorted_docs:
                if filepath not in current_paths:
                    processable_docs[filepath] = data
                    if len(processable_docs) >= self._scope_filter_settings.min_docs_threshold:
                        break

            analytics["min_threshold_applied"] = True
            analytics["final_doc_files"] = len(processable_docs)

        # Early return if no processable changes
        if not processable_code:
            self._log_analytics(analytics, estimated_tokens=0)
            return DocSuggestions(changes_to_apply=[])

        # Check cache validity
        state_hash = self._repository.get_state_hash(
            code_change=processable_code,
            docs_change=processable_docs,
        )

        if self._repository.is_state_valid(state_hash):
            self._log_analytics(analytics, estimated_tokens=0, cached=True)
            return self._repository.get_suggestions()

        # Build prompt with adaptive formatting if enabled
        prompt = self._build_prompt(
            processable_docs=processable_docs,
            processable_code=processable_code,
        )

        # Estimate tokens (rough: chars / 4)
        estimated_tokens = len(prompt) // 4
        analytics["estimated_prompt_tokens"] = estimated_tokens
        analytics["prompt_char_count"] = len(prompt)

        # Log analytics before LLM call
        self._log_analytics(analytics, estimated_tokens=estimated_tokens)

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
        # Use adaptive formatting if enabled
        if self._scope_filter_settings.enable_adaptive_pruning:
            code_formatted = ChangeProcessor.format_changes_adaptive(
                processable_code,
                include_metadata=True,
                high_detail_threshold=self._scope_filter_settings.high_detail_threshold,
                medium_detail_threshold=self._scope_filter_settings.medium_detail_threshold,
            )
        else:
            code_formatted = ChangeProcessor.format_changes_for_prompt(
                processable_code,
                include_metadata=True,
            )

        return SUGGESTION_PROMPT.format(
            documentation=ChangeProcessor.format_changes_for_prompt(
                processable_docs,
                include_metadata=False,
            ),
            code_changes=code_formatted,
        )

    def _log_analytics(
        self,
        analytics: dict[str, Any],
        estimated_tokens: int,
        cached: bool = False,
    ) -> None:
        """Log optimization analytics.

        Args:
            analytics: Dictionary of analytics data
            estimated_tokens: Estimated token count
            cached: Whether result was from cache
        """
        import logging

        logger = logging.getLogger(__name__)

        # Calculate optimization ratios
        initial_code = analytics.get("initial_code_files", 0)
        final_code = analytics.get(
            "scope_filtered_code_files", analytics.get("processable_code_files", 0)
        )
        initial_docs = analytics.get("initial_doc_files", 0)
        final_docs = analytics.get(
            "final_doc_files",
            analytics.get("term_filtered_doc_files", analytics.get("processable_doc_files", 0)),
        )

        code_reduction = (
            ((initial_code - final_code) / initial_code * 100) if initial_code > 0 else 0
        )
        doc_reduction = (
            ((initial_docs - final_docs) / initial_docs * 100) if initial_docs > 0 else 0
        )

        status = "cached" if cached else "generated"

        logger.info(
            f"Suggestion optimization ({status}): "
            f"code={final_code}/{initial_code} ({code_reduction:.1f}% filtered), "
            f"docs={final_docs}/{initial_docs} ({doc_reduction:.1f}% filtered), "
            f"tokens≈{estimated_tokens:,}"
        )

        # Log detailed analytics at debug level
        logger.debug(f"Detailed analytics: {analytics}")


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
