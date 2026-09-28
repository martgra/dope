"""Services for scanning files and generating descriptions."""

import asyncio
import hashlib
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from dope.consumers.base import BaseConsumer
from dope.core.classification import ChangeMagnitude, FileClassifier, calculate_magnitude_score
from dope.core.doc_terms import DocTermIndex
from dope.core.usage import UsageTracker
from dope.models.settings import get_settings
from dope.repositories.json_state import JsonStateRepository
from dope.services.describer.describer_agents import (
    Deps,
    get_code_change_agent,
    get_doc_summarization_agent,
)
from dope.services.describer.prompts import SUMMARIZATION_TEMPLATE
from dope.services.judge import judge_diff

if TYPE_CHECKING:
    from dope.consumers.git_consumer import GitConsumer


logger = logging.getLogger(__name__)


class DescriberService:
    """Scan files, generate summaries, and persist their state."""

    def __init__(
        self,
        *,
        consumer: BaseConsumer,
        repository: JsonStateRepository,
        usage_tracker: UsageTracker | None = None,
        doc_term_index_path: Path | None = None,
        extract_term_patterns: bool = True,
    ) -> None:
        """Initialize the service with its I/O and summary dependencies."""
        self._consumer = consumer
        self._repository = repository
        self._usage_tracker = usage_tracker or UsageTracker()
        self._doc_term_index_path = doc_term_index_path
        self._extract_term_patterns = extract_term_patterns

    @property
    def consumer(self) -> BaseConsumer:
        """Get the file consumer."""
        return self._consumer

    @property
    def repository(self) -> JsonStateRepository:
        """Get the state repository."""
        return self._repository

    @property
    def usage_tracker(self) -> UsageTracker:
        """Get the usage tracker."""
        return self._usage_tracker

    def _scan_files(self) -> dict:
        """Scan documentation files and return their content hashes."""
        return {
            str(file_path): {"hash": hashlib.md5(self._consumer.get_content(file_path)).hexdigest()}
            for file_path in self._consumer.discover_files()
        }

    def _run_agent(self, file_path: str, content: bytes) -> dict:
        """Generate a documentation summary with the configured LLM agent."""
        prompt = SUMMARIZATION_TEMPLATE.format(
            file_path=file_path,
            content=content.decode("utf-8", errors="ignore"),
        )
        return (
            get_doc_summarization_agent()
            .run_sync(
                user_prompt=prompt,
                usage=self._usage_tracker.usage,
            )
            .output.model_dump()
        )

    async def _run_agent_async(self, file_path: str, content: bytes) -> dict:
        """Generate a documentation summary asynchronously."""
        prompt = SUMMARIZATION_TEMPLATE.format(
            file_path=file_path,
            content=content.decode("utf-8", errors="ignore"),
        )
        result = await get_doc_summarization_agent().run(
            user_prompt=prompt,
            usage=self._usage_tracker.usage,
        )
        return result.output.model_dump()

    def _load_state(self) -> dict:
        return self._repository.load()

    def _save_state(self, state: dict) -> None:
        self._repository.save(state)

    def build_term_index(self) -> bool:
        """Build the documentation term index when its state is stale."""
        if not self._doc_term_index_path:
            return False

        from dope.core.doc_terms import DocTermIndexBuilder

        builder = DocTermIndexBuilder(
            self._doc_term_index_path,
            extract_patterns=self._extract_term_patterns,
        )
        return builder.build_if_needed(self._load_state())

    def _update_state(self, new_items: dict, current_state: dict) -> dict:
        for key in list(current_state):
            if key not in new_items:
                del current_state[key]

        for key, value in new_items.items():
            if value.get("skipped"):
                current_state[key] = value
            elif key not in current_state or current_state[key].get("hash") != value["hash"]:
                current_state[key] = {
                    "hash": value["hash"],
                    "summary": None,
                    "priority": value.get("priority"),
                    "metadata": value.get("metadata", {}),
                }
            else:
                current_state[key]["priority"] = value.get("priority")
                current_state[key]["metadata"] = value.get("metadata", {})
        return current_state

    def scan(self) -> dict:
        """Update persisted state from discovered files."""
        updated_state = self._update_state(self._scan_files(), self._load_state())
        self._save_state(updated_state)
        return updated_state

    def get_state(self) -> dict:
        """Return current persisted state."""
        return self._load_state()

    def save_state(self, state: dict) -> None:
        """Save state for CLI compatibility."""
        self._save_state(state)

    def files_needing_summary(self) -> list[str]:
        """Return non-skipped files with no summary."""
        return [
            file_path
            for file_path, data in self._load_state().items()
            if not data.get("skipped") and data.get("summary") is None
        ]

    def describe_and_save(self, file_path: str) -> dict:
        """Describe a single pending file and persist the result."""
        state = self._load_state()
        state_item = state.get(file_path, {})
        if state_item.get("skipped") or state_item.get("summary"):
            return state_item
        state[file_path] = self.describe(file_path, state_item)
        self._save_state(state)
        return state[file_path]

    def describe(self, file_path: str, state_item: dict) -> dict:
        """Generate a summary unless the item is skipped or already summarized."""
        if state_item.get("skipped") or state_item.get("summary"):
            return state_item
        content = self._consumer.get_content(self._consumer.root_path / file_path)
        try:
            state_item["summary"] = self._run_agent(file_path, content)
        except Exception as error:
            logger.warning("Failed to generate summary for %s: %s", file_path, error)
            state_item["summary"] = None
        return state_item

    async def describe_async(self, file_path: str, state_item: dict) -> dict:
        """Generate a summary asynchronously unless it is already available."""
        if state_item.get("skipped") or state_item.get("summary"):
            return state_item
        content = self._consumer.get_content(self._consumer.root_path / file_path)
        try:
            state_item["summary"] = await self._run_agent_async(file_path, content)
        except Exception as error:
            logger.warning("Failed to generate summary for %s: %s", file_path, error)
            state_item["summary"] = None
        return state_item

    async def describe_files_parallel(
        self, file_paths: list[str], max_concurrency: int = 5
    ) -> dict[str, dict]:
        """Describe files concurrently and persist completed state."""
        state = self._load_state()
        semaphore = asyncio.Semaphore(max_concurrency)

        async def process_file(file_path: str) -> tuple[str, dict]:
            async with semaphore:
                item = state.get(file_path, {}).copy()
                return file_path, await self.describe_async(file_path, item)

        results: dict[str, dict] = {}
        completed = await asyncio.gather(
            *(process_file(path) for path in file_paths), return_exceptions=True
        )
        for result in completed:
            if isinstance(result, BaseException):
                logger.warning("Parallel describe failed for a file: %s", result)
                continue
            file_path, item = result
            results[file_path] = item
            state[file_path] = item
        self._save_state(state)
        return results


class CodeDescriberService(DescriberService):
    """Describer service configured for code scanning and filtering."""

    def __init__(
        self,
        *,
        consumer: "GitConsumer",
        repository: JsonStateRepository,
        classifier: "FileClassifier | None" = None,
        usage_tracker: UsageTracker | None = None,
        enable_filtering: bool = True,
        doc_term_index_path: Path | None = None,
        extract_term_patterns: bool = True,
    ) -> None:
        """Initialize code-specific scanning and summary strategies."""
        super().__init__(
            consumer=consumer,
            repository=repository,
            usage_tracker=usage_tracker,
            doc_term_index_path=doc_term_index_path,
            extract_term_patterns=extract_term_patterns,
        )
        self._git_consumer = consumer
        self._classifier = classifier or FileClassifier()
        self._enable_filtering = enable_filtering
        self._doc_term_index: DocTermIndex | None = None

        if doc_term_index_path and doc_term_index_path.exists():
            self._doc_term_index = DocTermIndex(doc_term_index_path)
            if not self._doc_term_index.load():
                self._doc_term_index = None

    @property
    def enable_filtering(self) -> bool:
        """Whether intelligent filtering is enabled."""
        return self._enable_filtering

    def should_process_file(self, file_path: Path) -> dict:
        """Decide whether a changed code file needs LLM processing."""
        if not self._enable_filtering:
            return {"process": True, "reason": "Filtering disabled", "priority": "NORMAL"}

        classification = self._classifier.classify(file_path)
        if classification.classification == "SKIP":
            return {
                "process": False,
                "reason": classification.reason,
                "priority": None,
                "metadata": {"classification": classification.classification},
            }

        try:
            magnitude = self._get_change_magnitude(file_path)
            self._apply_doc_term_boost(file_path, magnitude)
        except Exception as error:
            logger.warning(
                "Could not determine change magnitude for %s: %s. Processing anyway.",
                file_path,
                error,
            )
            return {
                "process": True,
                "reason": "Could not determine magnitude",
                "priority": classification.classification,
            }

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

        try:
            if not self._git_consumer.get_normalized_diff(file_path):
                return {
                    "process": False,
                    "reason": "Whitespace/formatting changes only",
                    "priority": None,
                    "metadata": {
                        "classification": classification.classification,
                        "magnitude": magnitude.score,
                    },
                }
        except Exception as error:
            logger.debug(
                "Could not normalize diff for %s: %s. Processing anyway.", file_path, error
            )

        metadata = {
            "classification": classification.classification,
            "magnitude": magnitude.score,
            "lines_added": magnitude.lines_added,
            "lines_deleted": magnitude.lines_deleted,
            "is_rename": magnitude.is_rename,
        }
        if magnitude.related_docs:
            metadata["related_docs"] = magnitude.related_docs
        return {
            "process": True,
            "reason": f"Significant change ({magnitude.total_lines} lines changed)",
            "priority": classification.classification,
            "metadata": metadata,
        }

    @staticmethod
    def _parse_numstat(diff_output: str) -> tuple[int, int]:
        """Extract added and deleted line counts from Git numstat output."""
        if not diff_output:
            return 0, 0
        parts = diff_output.strip().split("\n", maxsplit=1)[0].split("\t")
        if len(parts) < 2:
            return 0, 0
        added, deleted = parts[:2]
        return 0 if added == "-" else int(added), 0 if deleted == "-" else int(deleted)

    @staticmethod
    def _parse_rename_summary(rename_output: str) -> tuple[bool, int | None]:
        """Determine rename status and similarity from a Git summary."""
        if "rename" not in rename_output.lower():
            return False, None
        match = re.search(r"(\d+)%", rename_output)
        return True, int(match.group(1)) if match else None

    def _get_change_magnitude(self, file_path: Path) -> ChangeMagnitude:
        """Calculate a file's change magnitude from Git's diff output."""
        diff_output = self._git_consumer.repo.git.diff(
            self._git_consumer.base_branch,
            "-M90%",
            "--numstat",
            "--",
            str(file_path),
        )
        lines_added, lines_deleted = self._parse_numstat(diff_output)
        rename_output = self._git_consumer.repo.git.diff(
            self._git_consumer.base_branch,
            "-M90%",
            "--summary",
            "--",
            str(file_path),
        )
        is_rename, rename_similarity = self._parse_rename_summary(rename_output)
        return ChangeMagnitude(
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            total_lines=lines_added + lines_deleted,
            is_rename=is_rename,
            rename_similarity=rename_similarity,
            score=calculate_magnitude_score(
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                is_rename=is_rename,
                rename_similarity=rename_similarity,
            ),
        )

    def _apply_doc_term_boost(self, file_path: Path, magnitude: ChangeMagnitude) -> None:
        """Boost a score when the normalized diff matches indexed terms."""
        if self._doc_term_index is None or magnitude.total_lines == 0:
            return
        try:
            diff_content = self._git_consumer.get_normalized_diff(file_path).decode(
                "utf-8", errors="ignore"
            )
            doc_matches = self._doc_term_index.get_relevant_docs(diff_content)
            if not doc_matches:
                return
            magnitude.related_docs = [doc for doc, _ in doc_matches[:3]]
            boost_factor = min(1.5, 1.0 + sum(count for _, count in doc_matches) * 0.05)
            magnitude.score = min(1.0, magnitude.score * boost_factor)
        except Exception as error:
            logger.debug("Failed to apply doc term boost for %s: %s", file_path, error)

    def _scan_files(self) -> dict:
        """Scan changed code files and preserve filtering metadata."""
        file_hashes = {}
        for file_path in self._git_consumer.discover_files():
            if not self._enable_filtering:
                content = self._git_consumer.get_content(file_path)
                file_hashes[str(file_path)] = {"hash": hashlib.md5(content).hexdigest()}
                continue

            decision = self.should_process_file(file_path)
            if not decision["process"]:
                file_hashes[str(file_path)] = {
                    "hash": None,
                    "skipped": True,
                    "skip_reason": decision["reason"],
                    "metadata": decision.get("metadata", {}),
                }
                continue
            content = self._git_consumer.get_content(file_path)
            file_hashes[str(file_path)] = {
                "hash": hashlib.md5(content).hexdigest(),
                "priority": decision.get("priority"),
                "metadata": decision.get("metadata", {}),
            }
        return file_hashes

    def _run_agent(self, file_path: str, content: bytes) -> dict:
        """Generate a code-change summary with Git context."""
        prompt = SUMMARIZATION_TEMPLATE.format(
            file_path=file_path,
            content=content.decode("utf-8", errors="ignore"),
        )
        return (
            get_code_change_agent()
            .run_sync(
                user_prompt=prompt,
                deps=Deps(consumer=self._git_consumer),
                usage=self._usage_tracker.usage,
            )
            .output.model_dump()
        )

    async def _run_agent_async(self, file_path: str, content: bytes) -> dict:
        """Generate a code-change summary and (optionally) a Jev DiffJudgment.

        When ``settings.typesafe.api_key`` is set, the pydantic-ai summary
        agent and :func:`judge_diff` run concurrently against the same file
        and the typed judgment is attached under the ``judgment`` key. If the
        key is unset the judgment is skipped silently so the pipeline still
        works for users without TypeSafe.
        """
        prompt = SUMMARIZATION_TEMPLATE.format(
            file_path=file_path,
            content=content.decode("utf-8", errors="ignore"),
        )
        summary_task = get_code_change_agent().run(
            user_prompt=prompt,
            deps=Deps(consumer=self._git_consumer),
            usage=self._usage_tracker.usage,
        )
        if get_settings().typesafe.api_key is None:
            result = await summary_task
            return result.output.model_dump()

        diff_bytes = self._git_consumer.get_normalized_diff(Path(file_path))
        diff_text = diff_bytes.decode("utf-8", errors="ignore")
        # Jev calls run outside the shared UsageTracker so their per-file
        # request count (6 agents) doesn't exhaust pydantic-ai's default
        # per-run request_limit that the OpenAI summary agent inherits.
        judgment_task = judge_diff(diff_text)
        result, judgment = await asyncio.gather(summary_task, judgment_task)
        summary = result.output.model_dump()
        summary["judgment"] = judgment.model_dump()
        return summary
