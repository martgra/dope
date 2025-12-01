import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from dope.consumers.base import BaseConsumer
from dope.core.usage import UsageTracker
from dope.repositories.describer_state import DescriberRepository
from dope.services.describer.strategies import (
    AgentStrategy,
    DocAgentStrategy,
    DocScanStrategy,
    ScanStrategy,
)

if TYPE_CHECKING:
    from dope.consumers.git_consumer import GitConsumer
    from dope.core.classification import FileClassifier


logger = logging.getLogger(__name__)


class DescriberService:
    """Scanner service using repository pattern for state management.

    This service uses the Strategy pattern for scanning and description behaviors,
    allowing composition of different strategies without inheritance.

    Args:
        consumer: File consumer for discovering and reading files.
        repository: Repository for state persistence (required).
        usage_tracker: Optional tracker for LLM usage statistics.
        doc_term_index_path: Optional path to doc term index file.
        scan_strategy: Optional custom scan strategy (defaults to DocScanStrategy).
        agent_strategy: Optional custom agent strategy (defaults to DocAgentStrategy).
    """

    def __init__(
        self,
        *,
        consumer: BaseConsumer,
        repository: DescriberRepository,
        usage_tracker: UsageTracker | None = None,
        doc_term_index_path: Path | None = None,
        scan_strategy: ScanStrategy | None = None,
        agent_strategy: AgentStrategy | None = None,
    ):
        self._consumer = consumer
        self._repository = repository
        self._usage_tracker = usage_tracker or UsageTracker()
        self._doc_term_index_path = doc_term_index_path
        self._scan_strategy = scan_strategy or DocScanStrategy()
        self._agent_strategy = agent_strategy or DocAgentStrategy()

    @property
    def consumer(self) -> BaseConsumer:
        """Get the file consumer."""
        return self._consumer

    @property
    def repository(self) -> DescriberRepository:
        """Get the state repository."""
        return self._repository

    @property
    def usage_tracker(self) -> UsageTracker:
        """Get the usage tracker."""
        return self._usage_tracker

    @property
    def scan_strategy(self) -> ScanStrategy:
        """Get the scan strategy."""
        return self._scan_strategy

    @property
    def agent_strategy(self) -> AgentStrategy:
        """Get the agent strategy."""
        return self._agent_strategy

    def _compute_hash(self, file_path: Path) -> str:
        content = self._consumer.get_content(file_path)
        return hashlib.md5(content).hexdigest()

    def _scan_files(self) -> dict:
        """Scan files using the configured strategy."""
        return self._scan_strategy.scan_files(self._consumer)

    def _load_state(self) -> dict:
        """Load the scanner state using repository."""
        return self._repository.load()

    def _save_state(self, state: dict) -> None:
        """Save the state using repository."""
        self._repository.save(state)

    def build_term_index(self) -> bool:
        """Build and save doc term index from current state.

        This should be called explicitly after scanning documentation files.
        Only rebuilds if the index is stale or doesn't exist.

        Returns:
            True if index was rebuilt, False if cache was valid.
        """
        if not self._doc_term_index_path:
            return False

        from dope.core.doc_terms import DocTermIndexBuilder

        builder = DocTermIndexBuilder(self._doc_term_index_path)
        state = self._load_state()
        return builder.build_if_needed(state)

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
        old_state = self._load_state()
        new_items = self._scan_files()
        updated_state = self._update_state(new_items, old_state)
        self._save_state(updated_state)
        return updated_state

    def get_state(self) -> dict:
        """Return current state from repository."""
        return self._load_state()

    def save_state(self, state: dict) -> None:
        """Save state to repository (public method for CLI compatibility).

        Args:
            state: State dictionary to persist.
        """
        self._save_state(state)

    def files_needing_summary(self) -> list[str]:
        """Get list of file paths that need summaries generated.

        Returns files that:
        - Are not skipped
        - Have no summary yet

        Returns:
            List of file path strings needing summaries.
        """
        state = self._load_state()
        return [
            filepath
            for filepath, data in state.items()
            if not data.get("skipped") and data.get("summary") is None
        ]

    def describe_and_save(self, file_path: str) -> dict:
        """Describe a single file and persist the result.

        This method:
        1. Loads current state
        2. Generates summary for the file
        3. Saves updated state immediately

        Args:
            file_path: Path to the file to describe.

        Returns:
            Updated state item for the file.
        """
        state = self._load_state()
        state_item = state.get(file_path, {})

        # Skip if already has summary or is skipped
        if state_item.get("skipped") or state_item.get("summary"):
            return state_item

        # Generate summary
        updated_item = self.describe(file_path=file_path, state_item=state_item)

        # Persist immediately
        state[file_path] = updated_item
        self._save_state(state)

        return updated_item

    def describe(self, file_path, state_item) -> dict:
        """For each file with a missing summary, generate one using the agent.

        Skips files marked as skipped in the filtering phase.
        """
        # Skip files that were filtered out
        if state_item.get("skipped"):
            return state_item

        if not state_item["summary"]:
            content = self._consumer.get_content(self._consumer.root_path / file_path)
            try:
                state_item["summary"] = self._agent_strategy.run_agent(
                    file_path=file_path,
                    content=content,
                    usage_tracker=self._usage_tracker,
                    consumer=self._consumer,
                )
            except Exception as e:
                logger.warning("Failed to generate summary for %s: %s", file_path, e)
                state_item["summary"] = None
        return state_item

    async def describe_async(self, file_path: str, state_item: dict) -> dict:
        """Generate summary for a file asynchronously.

        Args:
            file_path: Path to the file.
            state_item: Current state item for the file.

        Returns:
            Updated state item with summary.
        """
        if state_item.get("skipped"):
            return state_item

        if not state_item["summary"]:
            content = self._consumer.get_content(self._consumer.root_path / file_path)
            try:
                state_item["summary"] = await self._agent_strategy.run_agent_async(
                    file_path=file_path,
                    content=content,
                    usage_tracker=self._usage_tracker,
                    consumer=self._consumer,
                )
            except Exception as e:
                logger.warning("Failed to generate summary for %s: %s", file_path, e)
                state_item["summary"] = None
        return state_item

    async def describe_files_parallel(
        self,
        file_paths: list[str],
        max_concurrency: int = 5,
    ) -> dict[str, dict]:
        """Describe multiple files in parallel and save results.

        Uses asyncio.Semaphore to limit concurrent LLM API calls.

        Args:
            file_paths: List of file paths to describe.
            max_concurrency: Maximum concurrent API calls (default: 5).

        Returns:
            Dictionary mapping file paths to their updated state items.
        """
        import asyncio

        state = self._load_state()
        semaphore = asyncio.Semaphore(max_concurrency)
        results: dict[str, dict] = {}

        async def process_file(file_path: str) -> tuple[str, dict]:
            async with semaphore:
                state_item = state.get(file_path, {}).copy()
                if state_item.get("skipped") or state_item.get("summary"):
                    return file_path, state_item
                updated = await self.describe_async(file_path, state_item)
                return file_path, updated

        tasks = [process_file(fp) for fp in file_paths]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for result in completed:
            if isinstance(result, Exception):
                logger.warning("Parallel describe failed for a file: %s", result)
                continue
            file_path, updated_item = result
            results[file_path] = updated_item
            state[file_path] = updated_item

        self._save_state(state)
        return results


class CodeDescriberService(DescriberService):
    """Code describer service with intelligent filtering.

    This service handles code file scanning and description, with support for
    intelligent filtering based on file classification and change magnitude.

    Uses CodeScanStrategy and CodeAgentStrategy via composition instead of
    method overriding.

    Args:
        consumer: GitConsumer instance for code operations.
        repository: Repository for state persistence (required).
        classifier: File classifier for determining processing priority.
        usage_tracker: Optional tracker for LLM usage statistics.
        enable_filtering: Enable intelligent pre-filtering (default: True).
        doc_term_index_path: Optional path to doc term index for context-aware scoring.
    """

    def __init__(
        self,
        *,
        consumer: "GitConsumer",
        repository: DescriberRepository,
        classifier: "FileClassifier | None" = None,
        usage_tracker: UsageTracker | None = None,
        enable_filtering: bool = True,
        doc_term_index_path: Path | None = None,
    ):
        from dope.core.classification import FileClassifier
        from dope.services.describer.strategies import CodeAgentStrategy, CodeScanStrategy

        # Create strategies for code scanning and description
        scan_strategy = CodeScanStrategy(
            consumer=consumer,
            classifier=classifier or FileClassifier(),
            enable_filtering=enable_filtering,
            doc_term_index_path=doc_term_index_path,
        )
        agent_strategy = CodeAgentStrategy(consumer=consumer)

        super().__init__(
            consumer=consumer,
            repository=repository,
            usage_tracker=usage_tracker,
            doc_term_index_path=doc_term_index_path,
            scan_strategy=scan_strategy,
            agent_strategy=agent_strategy,
        )

        # Store reference for backward compatibility with tests
        self._git_consumer: GitConsumer = consumer

    @property
    def enable_filtering(self) -> bool:
        """Whether intelligent filtering is enabled."""
        from dope.services.describer.strategies import CodeScanStrategy

        if isinstance(self._scan_strategy, CodeScanStrategy):
            return self._scan_strategy.enable_filtering
        return False

    def should_process_file(self, file_path: Path) -> dict:
        """Decide if a file needs LLM processing using multiple signals.

        Delegates to the CodeScanStrategy.

        Args:
            file_path: Path to the file to evaluate

        Returns:
            dict with process decision, reason, priority, and metadata.
        """
        from dope.services.describer.strategies import CodeScanStrategy

        if isinstance(self._scan_strategy, CodeScanStrategy):
            return self._scan_strategy.should_process_file(file_path)
        return {"process": True, "reason": "No filtering strategy", "priority": "NORMAL"}
