"""ScopeService orchestrates project-complexity, scope creation, and doc alignment."""

import asyncio
import logging
from pathlib import Path

from dope.consumers.doc_consumer import DocConsumer
from dope.consumers.git_consumer import GitConsumer
from dope.core.progress import track
from dope.core.usage import UsageTracker
from dope.llms.usage_limits import DEFAULT_USAGE_LIMITS
from dope.models.domain.scope import ScopeTemplate, SuggestedChange
from dope.models.settings import get_settings
from dope.prompts import PromptRegistry
from dope.services.judge.judge_service import judge_alignment_preserves_scope
from dope.services.scoper.scoper_agents import (
    get_doc_aligner_agent,
    get_project_complexity_agent,
    get_scope_creator_agent,
)

logger = logging.getLogger(__name__)


class ScopeService:
    """ScopeService."""

    def __init__(
        self,
        doc_consumer: DocConsumer,
        git_consumer: GitConsumer,
        usage_tracker: UsageTracker | None = None,
    ):
        """Initialize ScopeService.

        Args:
            doc_consumer (DocConsumer): Consumer to interact with documentation.
            git_consumer (GitConsumer): Consumer to interact with code.
            usage_tracker (UsageTracker): Optional usage tracker for LLM token tracking.
        """
        self.doc_consumer = doc_consumer
        self.git_consumer = git_consumer
        self.usage_tracker = usage_tracker or UsageTracker()

    @staticmethod
    def _map_paths_to_sections(doc_scope: ScopeTemplate, section_paths: dict[str, str]) -> None:
        for doc_name, file_path in section_paths.items():
            for key, doc in doc_scope.documentation_structure.items():
                if key == doc_name:
                    doc.implemented_in_path = file_path

    def get_doc_overview(self) -> str:
        """Return document structure as string-tree.

        Returns:
            str: String representation of the document structure.
        """
        paths = self.doc_consumer.discover_files()
        return self.doc_consumer.get_structure(paths)

    def get_metadata(self):
        """Retrieves metadata from the Git repository.

        Returns:
            CodeMetadata: Repository metadata information.
        """
        metadata = self.git_consumer.get_metadata()
        return metadata

    def get_code_overview(self):
        """Retrieves the code structure as a string representation.

        Returns:
            str: String representation of the code structure.
        """
        paths = self.git_consumer.discover_files(mode="all")
        return self.git_consumer.get_structure(paths)

    def get_complexity(self, repo_structure, repo_metadata):
        """Evaluates the complexity of the project based on structure and metadata.

        Args:
            repo_structure (str): String representation of the repository structure.
            repo_metadata (dict): Repository metadata information.

        Returns:
            str: Complexity analysis of the project.
        """
        complexity = (
            get_project_complexity_agent()
            .run_sync(
                user_prompt=PromptRegistry.get("scope.complexity_user_template").render(
                    structure=repo_structure, metadata=repo_metadata
                ),
                usage=self.usage_tracker.usage,
                usage_limits=DEFAULT_USAGE_LIMITS,
            )
            .output
        )
        return complexity

    def suggest_structure(self, scope: ScopeTemplate, doc_structure: str, code_structure: str):
        """Suggests a documentation structure based on code and existing docs.

        Args:
            scope (ScopeTemplate): The documentation scope template.
            doc_structure (str): String representation of the document structure.
            code_structure (str): String representation of the code structure.

        Returns:
            ScopeTemplate: Updated scope with suggested structure.
        """
        prompt = f"""
        Here is the doc overview:
        {doc_structure}

        Here is the code overview:
        {code_structure}

        Here is the scope:
        {scope.model_dump_json(indent=2)}

        Here are the document keys to be filled into the dict {scope.get_all_documents()}:

        Based on this information, suggest a structure for the documentation where you map
        existing paths in the implemented doc structure to documents to relevant documents in
        the structure.
        """
        result = (
            get_scope_creator_agent()
            .run_sync(
                user_prompt=prompt,
                usage=self.usage_tracker.usage,
                usage_limits=DEFAULT_USAGE_LIMITS,
            )
            .output
        )
        self._map_paths_to_sections(scope, result)
        return scope

    @staticmethod
    def _check_and_read_doc(filepath: Path) -> str:
        filepath = Path(filepath)
        content = ""
        if filepath.is_file():
            with filepath.open() as file:
                content = file.read()
        return content

    @staticmethod
    def _create_file_and_path(filepath: Path, content: str):
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("w") as file:
            file.write(content)

    def _modify_or_create_doc(self, scope: ScopeTemplate):
        gate_enabled = get_settings().scope_filter.enable_align_minimality_gate
        scope_json = scope.model_dump_json(indent=2)
        changes_to_other_files: list[SuggestedChange] = []
        for _, doc in track(
            scope.documentation_structure.items(),
            description="Aligning changes to current doc structure",
        ):
            content = self._check_and_read_doc(
                Path(doc.implemented_in_path) if doc.implemented_in_path else Path(".")
            )
            prompt = PromptRegistry.get("scope.change_file_user_template").render(
                scope=scope_json,
                filepath=str(doc.implemented_in_path),
                file_content=content,
            )
            response = get_doc_aligner_agent().run_sync(
                user_prompt=prompt,
                usage=self.usage_tracker.usage,
                usage_limits=DEFAULT_USAGE_LIMITS,
            )
            suggested_structure = response.output
            content_to_write = self._gate_aligned_content(
                enabled=gate_enabled,
                scope_json=scope_json,
                filepath=str(doc.implemented_in_path),
                original=content,
                aligned=suggested_structure.content,
            )
            self._create_file_and_path(
                Path(doc.implemented_in_path) if doc.implemented_in_path else Path("."),
                content_to_write,
            )
            changes_to_other_files.extend(suggested_structure.changes_in_other_files)
        return changes_to_other_files

    def _gate_aligned_content(
        self,
        enabled: bool,
        scope_json: str,
        filepath: str,
        original: str,
        aligned: str,
    ) -> str:
        """Run the post-aligner minimality gate; fall back to original on fail.

        Returns the string that should actually be written to disk. When the
        gate is disabled, this is always the aligner output. When enabled,
        Jev is asked to confirm the rewrite is minimal versus the scope; a
        false answer means the aligner over-rewrote and the caller keeps
        the original file.
        """
        if not enabled:
            return aligned
        preserved = asyncio.run(
            judge_alignment_preserves_scope(
                scope=scope_json,
                original_content=original,
                aligned_content=aligned,
                usage_tracker=self.usage_tracker,
            )
        )
        if preserved:
            return aligned
        logger.info(
            "Minimality gate rejected aligner rewrite for %s; keeping original.",
            filepath,
        )
        return original

    def _implement_changes(self, changes_to_other_files: list[SuggestedChange]):
        for change in track(changes_to_other_files, description="Moving content between files."):
            doc_content = self._check_and_read_doc(Path(change.filepath))
            response = get_doc_aligner_agent().run_sync(
                user_prompt=PromptRegistry.get("scope.move_content_user_template").render(
                    instructions=change.instructions,
                    content=change.content,
                    doc_content=doc_content,
                ),
                usage=self.usage_tracker.usage,
                usage_limits=DEFAULT_USAGE_LIMITS,
            )
            aligned_doc = response.output
            self._create_file_and_path(Path(change.filepath), aligned_doc.content)

    def apply_scope(self, scope: ScopeTemplate):
        """Applies the scope to the documentation structure.

        This method maps sections to paths, creates necessary directories,
        and generates or updates files according to the documentation scope.

        Args:
            scope (ScopeTemplate): The documentation scope template to apply.
        """
        changes_to_other_files = self._modify_or_create_doc(scope)
        self._implement_changes(changes_to_other_files)
