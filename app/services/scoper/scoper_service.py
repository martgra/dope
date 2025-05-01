from pathlib import Path

from app.consumers.doc_consumer import DocConsumer
from app.consumers.git_consumer import GitConsumer
from app.models.domain.scope_template import ScopeTemplate
from app.services.scoper.prompts import CHANGE_FILE_PROMPT, PROMPT
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

    @staticmethod
    def _map_paths_to_sections(doc_scope: ScopeTemplate, section_paths: dict[str, str]) -> None:
        section_map = {}
        for doc_key, doc in doc_scope.documentation_structure.items():
            for section_name, section in doc.sections.items():
                section_map[(doc_key, section_name)] = section

        for section_name, file_path in section_paths.items():
            for (_doc_key, doc_section_name), section in section_map.items():
                if doc_section_name == section_name:
                    section.implemented_in_path = file_path

    @staticmethod
    def _map_sections_to_paths(doc_scope: ScopeTemplate) -> dict[str, list[dict]]:
        path_to_sections = {}

        for _, doc in doc_scope.documentation_structure.items():
            for _, section in doc.sections.items():
                if section.implemented_in_path:
                    file_path = section.implemented_in_path
                    if file_path not in path_to_sections:
                        path_to_sections[file_path] = []

                    path_to_sections[file_path].append(section)

        return path_to_sections

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
        return project_complexity_agent.run_sync(
            user_prompt=PROMPT.format(structure=repo_structure, metadata=repo_metadata)
        ).output

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

        Here are the section keys to be filled into the dict {scope.get_all_sections()}:

        Based on this information, suggest a structure for the documentation.
        """
        result = scope_creator_agent.run_sync(user_prompt=prompt).output
        self._map_paths_to_sections(scope, result)
        return scope

    def apply_scope(self, scope: ScopeTemplate):
        """Applies the scope to the documentation structure.

        This method maps sections to paths, creates necessary directories,
        and generates or updates files according to the documentation scope.

        Args:
            scope (ScopeTemplate): The documentation scope template to apply.
        """
        path_to_section = self._map_sections_to_paths(scope)

        for path, sections in path_to_section.items():
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.is_file():
                with path.open() as file:
                    content = file.read()
            else:
                content = ""

            prompt = CHANGE_FILE_PROMPT.format(
                scope=scope.model_dump_json(indent=2),
                section_definition="\n".join(
                    [section.model_dump_json(indent=2) for section in sections]
                ),
                file_content=content,
            )
            print(prompt)
            suggested_structure = doc_aligner_agent.run_sync(user_prompt=prompt).output
            with path.open("w") as file:
                file.write(suggested_structure)
