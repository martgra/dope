import hashlib
import json
from pathlib import Path

from pydantic.json import pydantic_encoder

from dope.core.usage import UsageTracker
from dope.models.domain.doc import DocSuggestions
from dope.services.suggester.prompts import FILE_SUMMARY_PROMPT, SUGGESTION_PROMPT
from dope.services.suggester.suggester_agents import get_suggester_agent


class DocChangeSuggester:
    """DocChangeSuggestor class."""

    def __init__(self, *, suggestion_state_path: Path, usage_tracker: UsageTracker | None = None):
        self._agent = None
        self.suggestion_state_path = Path(suggestion_state_path)
        self.usage_tracker = usage_tracker or UsageTracker()

    @property
    def agent(self):
        """Lazy-load the agent only when needed."""
        if self._agent is None:
            self._agent = get_suggester_agent()
        return self._agent

    @staticmethod
    def _filter_processable_files(state_dict: dict) -> dict:
        """Filter out skipped files and return only processable changes.

        Args:
            state_dict: State dictionary containing file information

        Returns:
            Filtered dictionary with only files that have summaries
        """
        processable = {}
        for filepath, data in state_dict.items():
            # Skip files marked as skipped
            if data.get("skipped"):
                continue

            # Skip files without summaries
            if not data.get("summary"):
                continue

            processable[filepath] = data

        return processable

    @staticmethod
    def _sort_by_priority(state_dict: dict) -> list[tuple[str, dict]]:
        """Sort files by priority (HIGH first, then NORMAL).

        Args:
            state_dict: State dictionary with priority metadata

        Returns:
            List of (filepath, data) tuples sorted by priority
        """
        items = list(state_dict.items())

        def priority_key(item):
            filepath, data = item
            priority = data.get("priority", "NORMAL")
            magnitude = data.get("metadata", {}).get("magnitude", 0.0)

            # Sort order: HIGH priority first, then by magnitude
            if priority == "HIGH":
                return (0, -magnitude)  # 0 for HIGH, negative magnitude for desc sort
            else:
                return (1, -magnitude)  # 1 for NORMAL

        return sorted(items, key=priority_key)

    @staticmethod
    def _prompt_formatter(state_dict: dict, include_metadata: bool = True) -> str:
        """Format state into prompt with optional metadata enrichment.

        Args:
            state_dict: State dictionary containing file information
            include_metadata: If True, include priority and magnitude in prompt

        Returns:
            Formatted prompt string
        """
        formatted_prompt = ""

        # Filter and sort
        processable = DocChangeSuggester._filter_processable_files(state_dict)
        sorted_files = DocChangeSuggester._sort_by_priority(processable)

        for filepath, data in sorted_files:
            # Build metadata context
            metadata_context = ""
            if include_metadata:
                priority = data.get("priority", "NORMAL")
                metadata = data.get("metadata", {})
                magnitude = metadata.get("magnitude", 0.0)
                lines_added = metadata.get("lines_added", 0)
                lines_deleted = metadata.get("lines_deleted", 0)

                metadata_context = f"\nPriority: {priority}"
                if magnitude > 0:
                    # Determine significance category
                    if magnitude > 0.7:
                        significance = "major"
                    elif magnitude > 0.4:
                        significance = "medium"
                    else:
                        significance = "minor"
                    metadata_context += (
                        f"\nChange Magnitude: {magnitude:.2f} (significance: {significance})"
                    )
                if lines_added > 0 or lines_deleted > 0:
                    metadata_context += f"\nLines Changed: +{lines_added} -{lines_deleted}"

            formatted_prompt += FILE_SUMMARY_PROMPT.format(
                file_path=filepath,
                metadata=metadata_context,
                summary=json.dumps(
                    data.get("summary"), indent=2, ensure_ascii=False, default=pydantic_encoder
                ),
            )
        return formatted_prompt

    def _check_get_state(self, state_hash: str):
        if not self.suggestion_state_path.is_file():
            return {}
        with self.suggestion_state_path.open() as file:
            state = json.load(file)
        if state_hash == state.get("hash"):
            return state
        else:
            return {}

    def get_state(self) -> DocSuggestions:
        """Return the suggested change state."""
        with self.suggestion_state_path.open() as file:
            return DocSuggestions.model_validate(json.load(file).get("suggestion"))

    def _get_state_hash(self, *, docs_change: dict, code_change: dict):
        return hashlib.md5(
            json.dumps(docs_change).encode("utf-8") + json.dumps(code_change).encode("utf-8")
        ).hexdigest()

    def _save_state(self, state):
        with self.suggestion_state_path.open("w") as file:
            json.dump(state, file, ensure_ascii=False, indent=True)

    def get_suggestions(self, *, docs_change, code_change, scope):
        """Get suggestions how to update doc.

        Filters out skipped files, prioritizes HIGH priority changes,
        and includes change magnitude metadata in the prompt.

        Args:
            docs_change: Dictionary of documentation changes
            code_change: Dictionary of code changes with metadata
            scope: Project scope information

        Returns:
            DocSuggestions with prioritized and filtered suggestions
        """
        # Filter processable files first
        processable_code = self._filter_processable_files(code_change)
        processable_docs = self._filter_processable_files(docs_change)

        # Early return if no processable changes
        if not processable_code:
            return DocSuggestions(changes_to_apply=[])

        state_hash = self._get_state_hash(
            code_change=processable_code, docs_change=processable_docs
        )
        suggestion_state = self._check_get_state(state_hash)

        if not suggestion_state:
            suggestion_state["hash"] = state_hash

            # Build enhanced prompt with metadata
            prompt = SUGGESTION_PROMPT.format(
                scope=scope,
                documentation=self._prompt_formatter(processable_docs, include_metadata=False),
                code_changes=self._prompt_formatter(processable_code, include_metadata=True),
            )

            suggestion = self.agent.run_sync(
                user_prompt=prompt,
                usage=self.usage_tracker.usage,
            ).output
            suggestion_state["suggestion"] = suggestion.model_dump()
            self._save_state(suggestion_state)
        else:
            suggestion = DocSuggestions.model_validate(suggestion_state.get("suggestion"))

        return suggestion
