import functools
from pathlib import Path

from pydantic_ai.usage import Usage

from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.core.progress import track
from app.models.domain.scope_template import ScopeTemplate, SuggestedChange
from app.services.scoper.prompts import CHANGE_FILE_PROMPT, MOVE_CONTENT_PROMPT, PROMPT
from app.services.scoper.scoper_agents import (
    doc_aligner_agent,
    project_complexity_agent,
    scope_creator_agent,
)


class ScopeService:
    """ScopeService."""

    def __init__(self, doc_consumer: DocConsumer, git_consumer: GitConsumer):
        """Initialize ScopeService.

        Args:
            doc_consumer (DocConsumer): Consumer to interact with documentation.
            git_consumer (GitConsumer): Consumer to interact with code.
        """
        self.doc_consumer = doc_consumer
        self.git_consumer = git_consumer
        self.usage = Usage()

    @staticmethod
    def _log_name(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            tokens_before = self.usage.total_tokens or 0
            result = func(self, *args, **kwargs)
            print(f"{func.__name__} tokens used: {self.usage.total_tokens - tokens_before}")
            return result

        return wrapper

    @staticmethod
    def _map_paths_to_sections(doc_scope: ScopeTemplate, section_paths: dict[str, str]) -> None:
        for doc_name, file_path in section_paths.items():
            for key, doc in doc_scope.documentation_structure.items():
                if key == doc_name:
                    doc.implemented_in_path = file_path

    @staticmethod
    def _map_sections_to_paths(doc_scope: ScopeTemplate) -> dict[str, list[dict]]:
        path_to_docs = {}

        for _, doc in doc_scope.documentation_structure.items():
            if doc.implemented_in_path:
                file_path = doc.implemented_in_path
                if file_path not in path_to_docs:
                    path_to_docs[file_path] = []
                path_to_docs[file_path].append(doc)

        return path_to_docs

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

    @_log_name
    def get_complexity(self, repo_structure, repo_metadata):
        """Evaluates the complexity of the project based on structure and metadata.

        Args:
            repo_structure (str): String representation of the repository structure.
            repo_metadata (dict): Repository metadata information.

        Returns:
            str: Complexity analysis of the project.
        """
        complexity = project_complexity_agent.run_sync(
            user_prompt=PROMPT.format(structure=repo_structure, metadata=repo_metadata),
            usage=self.usage,
        ).output
        return complexity

    @_log_name
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
        result = scope_creator_agent.run_sync(user_prompt=prompt, usage=self.usage).output
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
        changes_to_other_files: list[SuggestedChange] = []
        for _, doc in track(
            scope.documentation_structure.items(),
            description="Aligning changes to current doc structure",
        ):
            content = self._check_and_read_doc(doc.implemented_in_path)
            prompt = CHANGE_FILE_PROMPT.format(
                scope=scope.model_dump_json(indent=2),
                filepath=str(doc.implemented_in_path),
                file_content=content,
            )
            response = doc_aligner_agent.run_sync(user_prompt=prompt, usage=self.usage)
            suggested_structure = response.output
            self._create_file_and_path(doc.implemented_in_path, suggested_structure.content)
            changes_to_other_files.extend(suggested_structure.changes_in_other_files)
        return changes_to_other_files

    def _implement_changes(self, changes_to_other_files: list[SuggestedChange]):
        for change in track(changes_to_other_files, description="Moving content between files."):
            doc_content = self._check_and_read_doc(change.filepath)
            response = doc_aligner_agent.run_sync(
                user_prompt=MOVE_CONTENT_PROMPT.format(
                    instructions=change.instructions,
                    content=change.content,
                    doc_content=doc_content,
                ),
                usage=self.usage,
            )
            aligned_doc = response.output
            self._create_file_and_path(change.filepath, aligned_doc.content)

    @_log_name
    def apply_scope(self, scope: ScopeTemplate):
        """Applies the scope to the documentation structure.

        This method maps sections to paths, creates necessary directories,
        and generates or updates files according to the documentation scope.

        Args:
            scope (ScopeTemplate): The documentation scope template to apply.
        """
        changes_to_other_files = self._modify_or_create_doc(scope)
        self._implement_changes(changes_to_other_files)
