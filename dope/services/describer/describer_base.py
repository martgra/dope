import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

from dope.consumers.base import BaseConsumer
from dope.core.usage import UsageTracker
from dope.services.describer.describer_agents import (
    Deps,
    get_code_change_agent,
    get_doc_summarization_agent,
)
from dope.services.describer.prompts import SUMMARIZATION_TEMPLATE

if TYPE_CHECKING:
    from dope.consumers.git_consumer import GitConsumer


class DescriberService:
    """Scanner service."""

    def __init__(
        self,
        consumer: BaseConsumer,
        state_filepath: Path | None = None,
        usage_tracker: UsageTracker | None = None,
        doc_term_index_path: Path | None = None,
    ):
        self.consumer = consumer
        self.state_filepath = state_filepath
        self.usage_tracker = usage_tracker or UsageTracker()
        self.doc_term_index_path = doc_term_index_path

    def _compute_hash(self, file_path: Path) -> str:
        content = self.consumer.get_content(file_path)
        return hashlib.md5(content).hexdigest()

    def _scan_files(self) -> dict:
        file_hashes = {}
        for file_path in self.consumer.discover_files():
            file_hash = self._compute_hash(file_path)
            file_hashes[str(file_path)] = {"hash": file_hash}
        return file_hashes

    def load_state(self) -> dict:
        """Load the scanner state."""
        if self.state_filepath and self.state_filepath.exists():
            with self.state_filepath.open("r") as f:
                return json.load(f)
        return {}

    def save_state(self, state: dict):
        """Save the state of the scanner."""
        if self.state_filepath:
            self.state_filepath.parent.mkdir(parents=True, exist_ok=True)
            with self.state_filepath.open("w") as f:
                json.dump(state, f, ensure_ascii=False, indent=4)

        # Also build and save doc term index if configured (for doc scanner)
        if self.doc_term_index_path:
            self._build_and_save_term_index(state)

    def _build_and_save_term_index(self, state: dict):
        """Build term index from documentation state and save it.

        Args:
            state: Documentation state with summaries
        """
        from dope.core.doc_terms import DocTermIndex

        index = DocTermIndex(self.doc_term_index_path)

        # Only rebuild if state has changed
        if index.load() and not index.is_stale(state):
            return

        # Build from current state
        index.build_from_state(state)
        index.save()

    def _update_state(self, new_items: dict, current_state: dict) -> dict:
        """Update state handling both processed and skipped files."""
        for key in list(current_state.keys()):
            if key not in new_items:
                del current_state[key]

        for key, value in new_items.items():
            # Handle skipped files
            if value.get("skipped"):
                current_state[key] = value
                continue

            # Handle processed files
            if key not in current_state or current_state[key].get("hash") != value["hash"]:
                current_state[key] = {
                    "hash": value["hash"],
                    "summary": None,
                    "priority": value.get("priority"),
                    "metadata": value.get("metadata", {}),
                }
            else:
                # Preserve existing summary, update metadata
                current_state[key]["priority"] = value.get("priority")
                current_state[key]["metadata"] = value.get("metadata", {})

        return current_state

    def scan(self) -> dict:
        """Perform scanning by updating the state based on discovered files and their hashes."""
        old_state = self.load_state()
        new_items = self._scan_files()
        updated_state = self._update_state(new_items, old_state)
        self.save_state(updated_state)
        return updated_state

    def get_state(self) -> dict:
        """Return state."""
        return self.load_state()

    def _run_agent(self, prompt):
        return (
            get_doc_summarization_agent()
            .run_sync(
                user_prompt=prompt,
                usage=self.usage_tracker.usage,
            )
            .output.model_dump()
        )

    def describe(self, file_path, state_item) -> dict:
        """For each file with a missing summary, generate one using the agent.

        Skips files marked as skipped in the filtering phase.
        """
        # Skip files that were filtered out
        if state_item.get("skipped"):
            return state_item

        if not state_item["summary"]:
            content = self.consumer.get_content(self.consumer.root_path / file_path)
            prompt = SUMMARIZATION_TEMPLATE.format(file_path=file_path, content=content)
            try:
                state_item["summary"] = self._run_agent(prompt=prompt)
            except Exception:
                state_item["summary"] = None
        return state_item


class CodeDescriberService(DescriberService):
    """Code describer service with intelligent filtering."""

    def __init__(
        self,
        consumer: "GitConsumer",
        state_filepath: Path | None = None,
        usage_tracker: UsageTracker | None = None,
        enable_filtering: bool = True,
        doc_term_index_path: Path | None = None,
    ):
        """Initialize with GitConsumer specifically.

        Args:
            consumer: GitConsumer instance for code operations
            state_filepath: Path to state file for caching
            usage_tracker: Tracker for LLM usage statistics
            enable_filtering: Enable intelligent pre-filtering (default: True)
            doc_term_index_path: Optional path to doc term index for context-aware scoring
        """
        super().__init__(
            consumer=consumer,
            state_filepath=state_filepath,
            usage_tracker=usage_tracker,
        )
        self.consumer: GitConsumer = consumer  # Type narrowing for this subclass
        self.enable_filtering = enable_filtering
        self.doc_term_index = None

        # Load doc term index if available
        if doc_term_index_path and doc_term_index_path.exists():
            from dope.core.doc_terms import DocTermIndex

            self.doc_term_index = DocTermIndex(doc_term_index_path)
            if self.doc_term_index.load():
                # Successfully loaded
                pass
            else:
                # Failed to load, disable
                self.doc_term_index = None

    def should_process_file(self, file_path: Path) -> dict:
        """Decide if a file needs LLM processing using multiple signals.

        Combines:
        - Path-based classification (test files, lock files, etc.)
        - Change magnitude analysis (lines changed, significance score)
        - Whitespace normalization (formatting-only changes)
        - Service-specific thresholds

        Args:
            file_path: Path to the file to evaluate

        Returns:
            dict with keys:
                - process (bool): Whether to process this file
                - reason (str): Human-readable reason for decision
                - priority (str|None): Priority level if processing
                - metadata (dict|None): Additional classification metadata
        """
        if not self.enable_filtering:
            return {"process": True, "reason": "Filtering disabled", "priority": "NORMAL"}

        # Step 1: Path-based classification (fast, no git operations)
        classification = self.consumer.classify_file_by_path(file_path)

        if classification.classification == "SKIP":
            return {
                "process": False,
                "reason": classification.reason,
                "priority": None,
                "metadata": {"classification": classification.classification},
            }

        # Step 2: Change magnitude analysis
        try:
            magnitude = self.consumer.get_change_magnitude(file_path)

            # Apply doc term relevance boost if index is available
            if self.doc_term_index and magnitude.total_lines > 0:
                try:
                    # Get normalized diff for term matching
                    diff_content = self.consumer.get_normalized_diff(file_path).decode(
                        "utf-8", errors="ignore"
                    )
                    doc_matches = self.doc_term_index.get_relevant_docs(diff_content)

                    if doc_matches:
                        # Extract just doc paths
                        magnitude.related_docs = [doc for doc, _ in doc_matches[:3]]

                        # Boost score based on documentation relevance
                        match_count = sum(count for _, count in doc_matches)
                        boost_factor = min(1.5, 1.0 + (match_count * 0.05))
                        magnitude.score = min(1.0, magnitude.score * boost_factor)
                except Exception:
                    pass

        except Exception:
            # If we can't get magnitude, process it to be safe
            return {
                "process": True,
                "reason": "Could not determine magnitude",
                "priority": classification.classification,
            }

        # Skip pure renames with minimal changes
        if magnitude.is_rename and magnitude.rename_similarity and magnitude.rename_similarity > 95:
            return {
                "process": False,
                "reason": f"Pure rename ({magnitude.rename_similarity}% similarity)",
                "priority": None,
                "metadata": {
                    "classification": classification.classification,
                    "magnitude": magnitude.score,
                    "rename_similarity": magnitude.rename_similarity,
                },
            }

        # Skip trivial changes unless it's a high-priority file
        if magnitude.score < 0.2 and classification.classification != "HIGH":
            return {
                "process": False,
                "reason": (
                    f"Trivial change ({magnitude.total_lines} lines, score: {magnitude.score:.2f})"
                ),
                "priority": None,
                "metadata": {
                    "classification": classification.classification,
                    "magnitude": magnitude.score,
                    "lines_changed": magnitude.total_lines,
                },
            }

        # Step 3: Check for whitespace-only changes
        try:
            normalized_diff = self.consumer.get_normalized_diff(file_path)
            if len(normalized_diff) == 0:
                return {
                    "process": False,
                    "reason": "Whitespace/formatting changes only",
                    "priority": None,
                    "metadata": {
                        "classification": classification.classification,
                        "magnitude": magnitude.score,
                    },
                }
        except Exception:
            # If normalization fails, continue processing
            pass

        # File should be processed
        priority = classification.classification
        metadata = {
            "classification": classification.classification,
            "magnitude": magnitude.score,
            "lines_added": magnitude.lines_added,
            "lines_deleted": magnitude.lines_deleted,
            "is_rename": magnitude.is_rename,
        }

        # Include doc relevance if available
        if magnitude.related_docs:
            metadata["related_docs"] = magnitude.related_docs

        return {
            "process": True,
            "reason": f"Significant change ({magnitude.total_lines} lines changed)",
            "priority": priority,
            "metadata": metadata,
        }

    def _scan_files(self) -> dict:
        """Scan files with intelligent filtering.

        Overrides parent to add pre-filtering before hash computation.
        Skipped files are recorded in state for transparency.
        """
        file_hashes = {}
        discovered_files = self.consumer.discover_files()

        for file_path in discovered_files:
            if self.enable_filtering:
                decision = self.should_process_file(file_path)

                if not decision["process"]:
                    # Record skipped files in state for debugging/metrics
                    file_hashes[str(file_path)] = {
                        "hash": None,
                        "skipped": True,
                        "skip_reason": decision["reason"],
                        "metadata": decision.get("metadata", {}),
                    }
                    continue

                # Store decision metadata for later use
                file_hash = self._compute_hash(file_path)
                file_hashes[str(file_path)] = {
                    "hash": file_hash,
                    "priority": decision.get("priority"),
                    "metadata": decision.get("metadata", {}),
                }
            else:
                # Original behavior when filtering is disabled
                file_hash = self._compute_hash(file_path)
                file_hashes[str(file_path)] = {"hash": file_hash}

        return file_hashes

    def _run_agent(self, prompt):
        return (
            get_code_change_agent()
            .run_sync(
                user_prompt=prompt,
                deps=Deps(consumer=self.consumer),
                usage=self.usage_tracker.usage,
            )
            .output.model_dump()
        )
