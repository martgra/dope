"""Strategy protocols and implementations for describer service.

This module implements the Strategy pattern to compose different scanning
and description behaviors without inheritance.
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from dope.consumers.base import BaseConsumer
from dope.core.classification import (
    ChangeMagnitude,
    FileClassifier,
    calculate_magnitude_score,
)
from dope.core.usage import UsageTracker
from dope.services.describer.describer_agents import (
    Deps,
    get_code_change_agent,
    get_doc_summarization_agent,
)
from dope.services.describer.prompts import SUMMARIZATION_TEMPLATE

if TYPE_CHECKING:
    from dope.consumers.git_consumer import GitConsumer


logger = logging.getLogger(__name__)


class ScanStrategy(Protocol):
    """Protocol for file scanning strategies.

    Implementations decide how to scan and filter files before processing.
    """

    @abstractmethod
    def scan_files(self, consumer: BaseConsumer) -> dict:
        """Scan files and return a dict of file paths to metadata.

        Args:
            consumer: File consumer for discovering files.

        Returns:
            Dict mapping file paths to metadata including:
            - hash: File content hash (or None if skipped)
            - skipped: Whether file was filtered out
            - skip_reason: Why file was skipped
            - priority: Processing priority
            - metadata: Additional classification data
        """
        ...


class AgentStrategy(Protocol):
    """Protocol for LLM agent strategies.

    Implementations define how to run the LLM agent for different content types.
    """

    @abstractmethod
    def run_agent(
        self,
        file_path: str,
        content: bytes,
        usage_tracker: UsageTracker,
        consumer: BaseConsumer | None = None,
    ) -> dict:
        """Run the appropriate LLM agent to generate a summary.

        Args:
            file_path: Path to the file being processed.
            content: File content as bytes.
            usage_tracker: Tracker for LLM usage statistics.
            consumer: Optional consumer for additional context.

        Returns:
            Summary dict from the LLM agent.
        """
        ...


@dataclass
class DocScanStrategy:
    """Scan strategy for documentation files.

    Simple scanning without filtering - all discovered docs are processed.
    """

    def scan_files(self, consumer: BaseConsumer) -> dict:
        """Scan all documentation files without filtering.

        Args:
            consumer: Doc consumer for discovering files.

        Returns:
            Dict mapping file paths to hash metadata.
        """
        import hashlib

        file_hashes = {}
        for file_path in consumer.discover_files():
            content = consumer.get_content(file_path)
            file_hash = hashlib.md5(content).hexdigest()
            file_hashes[str(file_path)] = {"hash": file_hash}
        return file_hashes


@dataclass
class CodeScanStrategy:
    """Scan strategy for code files with intelligent filtering.

    Uses classification and change magnitude analysis to decide
    which files need LLM processing.

    Args:
        consumer: Git consumer for code operations.
        classifier: File classifier for path-based decisions.
        enable_filtering: Whether to apply filtering rules.
        doc_term_index_path: Optional path to doc term index for relevance boosting.
    """

    consumer: "GitConsumer"
    classifier: FileClassifier | None = None
    enable_filtering: bool = True
    doc_term_index_path: Path | None = None
    _doc_term_index: object | None = None

    def __post_init__(self):
        """Initialize classifier and load doc term index."""
        if self.classifier is None:
            self.classifier = FileClassifier()

        # Load doc term index if available
        if self.doc_term_index_path and self.doc_term_index_path.exists():
            from dope.core.doc_terms import DocTermIndex

            self._doc_term_index = DocTermIndex(self.doc_term_index_path)
            if not self._doc_term_index.load():
                self._doc_term_index = None

    def _get_change_magnitude(self, file_path: Path) -> ChangeMagnitude:
        """Calculate the magnitude of changes in a file.

        Analyzes git diff to determine:
        - Lines added/deleted
        - Whether file was renamed
        - Rename similarity percentage
        - Overall significance score

        Args:
            file_path: Path to analyze.

        Returns:
            ChangeMagnitude with detailed change metrics.
        """
        import re

        repo = self.consumer.repo
        base_branch = self.consumer.base_branch

        # Get diff with rename detection
        diff_output = repo.git.diff(
            base_branch,
            "-M90%",  # Detect renames with 90% similarity threshold
            "--numstat",  # Get line counts
            "--",
            str(file_path),
        )

        # Parse numstat output: "added\tdeleted\tfilename"
        lines_added = 0
        lines_deleted = 0
        is_rename = False
        rename_similarity = None

        if diff_output:
            lines = diff_output.strip().split("\n")
            if lines:
                parts = lines[0].split("\t")
                if len(parts) >= 2:
                    # Handle binary files (marked as '-')
                    added_str = parts[0]
                    deleted_str = parts[1]

                    lines_added = 0 if added_str == "-" else int(added_str)
                    lines_deleted = 0 if deleted_str == "-" else int(deleted_str)

        # Check for rename/move
        rename_output = repo.git.diff(base_branch, "-M90%", "--summary", "--", str(file_path))

        if "rename" in rename_output.lower():
            is_rename = True
            # Try to extract similarity percentage
            match = re.search(r"(\d+)%", rename_output)
            if match:
                rename_similarity = int(match.group(1))

        # Calculate significance score using shared function
        total_lines = lines_added + lines_deleted
        score = calculate_magnitude_score(
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            is_rename=is_rename,
            rename_similarity=rename_similarity,
        )

        return ChangeMagnitude(
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            total_lines=total_lines,
            is_rename=is_rename,
            rename_similarity=rename_similarity,
            score=score,
        )

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
        classification = self.classifier.classify(file_path)

        if classification.classification == "SKIP":
            return {
                "process": False,
                "reason": classification.reason,
                "priority": None,
                "metadata": {"classification": classification.classification},
            }

        # Step 2: Change magnitude analysis
        try:
            magnitude = self._get_change_magnitude(file_path)

            # Apply doc term relevance boost if index is available
            if self._doc_term_index and magnitude.total_lines > 0:
                try:
                    # Get normalized diff for term matching
                    diff_content = self.consumer.get_normalized_diff(file_path).decode(
                        "utf-8", errors="ignore"
                    )
                    doc_matches = self._doc_term_index.get_relevant_docs(diff_content)

                    if doc_matches:
                        # Extract just doc paths
                        magnitude.related_docs = [doc for doc, _ in doc_matches[:3]]

                        # Boost score based on documentation relevance
                        match_count = sum(count for _, count in doc_matches)
                        boost_factor = min(1.5, 1.0 + (match_count * 0.05))
                        magnitude.score = min(1.0, magnitude.score * boost_factor)
                except Exception as e:
                    logger.debug("Failed to apply doc term boost for %s: %s", file_path, e)

        except Exception as e:
            # If we can't get magnitude, process it to be safe
            logger.warning(
                "Could not determine change magnitude for %s: %s. Processing anyway.",
                file_path,
                e,
            )
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
        except Exception as e:
            # If normalization fails, continue processing
            logger.debug("Could not normalize diff for %s: %s. Processing anyway.", file_path, e)

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

    def scan_files(self, consumer: BaseConsumer) -> dict:
        """Scan files with intelligent filtering.

        Args:
            consumer: Git consumer for file discovery (ignored, uses self.consumer).

        Returns:
            Dict mapping file paths to metadata.
        """
        import hashlib

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
                content = self.consumer.get_content(file_path)
                file_hash = hashlib.md5(content).hexdigest()
                file_hashes[str(file_path)] = {
                    "hash": file_hash,
                    "priority": decision.get("priority"),
                    "metadata": decision.get("metadata", {}),
                }
            else:
                # Original behavior when filtering is disabled
                content = self.consumer.get_content(file_path)
                file_hash = hashlib.md5(content).hexdigest()
                file_hashes[str(file_path)] = {"hash": file_hash}

        return file_hashes


@dataclass
class DocAgentStrategy:
    """Agent strategy for documentation summarization.

    Uses the doc summarization agent to generate structured summaries.
    """

    def run_agent(
        self,
        file_path: str,
        content: bytes,
        usage_tracker: UsageTracker,
        consumer: BaseConsumer | None = None,
    ) -> dict:
        """Run doc summarization agent.

        Args:
            file_path: Path to the documentation file.
            content: File content as bytes.
            usage_tracker: Tracker for LLM usage statistics.
            consumer: Not used for doc agent.

        Returns:
            DocSummary dict from the agent.
        """
        prompt = SUMMARIZATION_TEMPLATE.format(
            file_path=file_path,
            content=content.decode("utf-8", errors="ignore"),
        )
        return (
            get_doc_summarization_agent()
            .run_sync(
                user_prompt=prompt,
                usage=usage_tracker.usage,
            )
            .output.model_dump()
        )

    async def run_agent_async(
        self,
        file_path: str,
        content: bytes,
        usage_tracker: UsageTracker,
        consumer: BaseConsumer | None = None,
    ) -> dict:
        """Run doc summarization agent asynchronously.

        Args:
            file_path: Path to the documentation file.
            content: File content as bytes.
            usage_tracker: Tracker for LLM usage statistics.
            consumer: Not used for doc agent.

        Returns:
            DocSummary dict from the agent.
        """
        prompt = SUMMARIZATION_TEMPLATE.format(
            file_path=file_path,
            content=content.decode("utf-8", errors="ignore"),
        )
        result = await get_doc_summarization_agent().run(
            user_prompt=prompt,
            usage=usage_tracker.usage,
        )
        return result.output.model_dump()


@dataclass
class CodeAgentStrategy:
    """Agent strategy for code change summarization.

    Uses the code change agent with git consumer context.
    """

    consumer: "GitConsumer"

    def run_agent(
        self,
        file_path: str,
        content: bytes,
        usage_tracker: UsageTracker,
        consumer: BaseConsumer | None = None,
    ) -> dict:
        """Run code change agent with git context.

        Args:
            file_path: Path to the code file.
            content: File content as bytes (diff content).
            usage_tracker: Tracker for LLM usage statistics.
            consumer: Git consumer for additional context (uses self.consumer).

        Returns:
            CodeChanges dict from the agent.
        """
        prompt = SUMMARIZATION_TEMPLATE.format(
            file_path=file_path,
            content=content.decode("utf-8", errors="ignore"),
        )
        return (
            get_code_change_agent()
            .run_sync(
                user_prompt=prompt,
                deps=Deps(consumer=self.consumer),
                usage=usage_tracker.usage,
            )
            .output.model_dump()
        )

    async def run_agent_async(
        self,
        file_path: str,
        content: bytes,
        usage_tracker: UsageTracker,
        consumer: BaseConsumer | None = None,
    ) -> dict:
        """Run code change agent asynchronously with git context.

        Args:
            file_path: Path to the code file.
            content: File content as bytes (diff content).
            usage_tracker: Tracker for LLM usage statistics.
            consumer: Git consumer for additional context (uses self.consumer).

        Returns:
            CodeChanges dict from the agent.
        """
        prompt = SUMMARIZATION_TEMPLATE.format(
            file_path=file_path,
            content=content.decode("utf-8", errors="ignore"),
        )
        result = await get_code_change_agent().run(
            user_prompt=prompt,
            deps=Deps(consumer=self.consumer),
            usage=usage_tracker.usage,
        )
        return result.output.model_dump()
