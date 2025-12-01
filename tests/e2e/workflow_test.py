"""End-to-end tests for complete workflows.

These tests verify full workflows from file discovery to output generation,
using mocked LLM agents but real file system operations.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dope.models.settings import CodeRepoSettings, DocSettings, Settings
from dope.models.domain.documentation import (
    ChangeSuggestion,
    DocSuggestions,
    SuggestedChange,
)
from dope.models.enums import ChangeType


class TestDocumentationScanWorkflow:
    """E2E tests for documentation scanning workflow."""

    @pytest.fixture
    def doc_project(self, temp_dir, temp_file):
        """Create a documentation project structure."""
        # Create documentation files
        temp_file("docs/readme.md", "# Project\n\nWelcome to the project.")
        temp_file("docs/guide.md", "# Guide\n\n## Installation\nRun `pip install`.")
        temp_file("docs/api/endpoints.md", "# API\n\n## GET /users")

        # Create excluded files that should not be scanned
        temp_file("docs/node_modules/pkg/readme.md", "# Package docs")

        return temp_dir

    @pytest.fixture
    def mock_scan_agent(self):
        """Create mock agent for scan operation."""
        agent = MagicMock()

        mock_output = MagicMock()
        mock_output.model_dump.return_value = {
            "sections": [
                {
                    "section_name": "Introduction",
                    "summary": "Introduces the project",
                    "references": [],
                }
            ]
        }

        mock_result = MagicMock()
        mock_result.output = mock_output
        agent.run_sync.return_value = mock_result

        return agent

    def test_scan_discovers_all_documentation(self, doc_project, temp_dir):
        """Test that scan discovers all documentation files."""
        from dope.consumers.doc_consumer import DocConsumer

        consumer = DocConsumer(
            doc_project / "docs",
            file_type_filter={".md"},
            exclude_dirs={"node_modules"},
        )

        files = consumer.discover_files()

        file_names = {f.name for f in files}
        assert "readme.md" in file_names
        assert "guide.md" in file_names
        assert "endpoints.md" in file_names
        # Excluded directory
        assert len([f for f in files if "node_modules" in str(f)]) == 0

    @patch("dope.services.describer.strategies.get_doc_summarization_agent")
    def test_scan_generates_summaries(
        self, mock_get_agent, doc_project, temp_dir, mock_scan_agent
    ):
        """Test full scan workflow generates summaries."""
        from dope.consumers.doc_consumer import DocConsumer
        from dope.repositories.describer_state import DescriberRepository
        from dope.services.describer.describer_base import DescriberService

        mock_get_agent.return_value = mock_scan_agent

        consumer = DocConsumer(
            doc_project / "docs",
            file_type_filter={".md"},
            exclude_dirs={"node_modules"},
        )

        repository = DescriberRepository(temp_dir / "doc-state.json")
        service = DescriberService(
            consumer=consumer,
            repository=repository,
        )

        # Run scan
        state = service.scan()

        # Describe one file
        for filepath, state_item in state.items():
            if state_item.get("summary") is None:
                state[filepath] = service.describe(filepath, state_item)
                break

        repository.save(state)

        # Verify state was saved
        assert (temp_dir / "doc-state.json").exists()
        saved_state = json.loads((temp_dir / "doc-state.json").read_text())
        assert len(saved_state) > 0


class TestCodeScanWorkflow:
    """E2E tests for code scanning workflow."""

    @pytest.fixture
    def code_project(self, git_repo):
        """Create a code project with changes."""
        repo_path, repo = git_repo

        # Add source files
        (repo_path / "src").mkdir()
        (repo_path / "src" / "main.py").write_text("def main():\n    pass\n")
        (repo_path / "src" / "utils.py").write_text("def helper():\n    return True\n")
        repo.index.add(["src/main.py", "src/utils.py"])
        repo.index.commit("Add source files")

        # Make changes - modify existing committed file
        (repo_path / "src" / "main.py").write_text(
            "def main():\n    print('hello')\n    return 0\n"
        )

        return repo_path, repo

    def test_code_scan_detects_changes(self, code_project):
        """Test that code scan detects uncommitted changes."""
        from dope.consumers.git_consumer import GitConsumer

        repo_path, _ = code_project
        consumer = GitConsumer(repo_path, "main")

        changed = consumer.discover_files(mode="diff")

        changed_names = {str(f) for f in changed}
        # main.py is modified (already committed then changed)
        assert "src/main.py" in changed_names

    def test_code_scan_classifies_files(self, code_project):
        """Test that code scan classifies files by priority."""
        from dope.core.classification import FileClassifier

        repo_path, _ = code_project

        # Use classifier directly (classification logic moved to services layer)
        classifier = FileClassifier()
        classification = classifier.classify(Path("test_main.py"))

        assert classification.classification == "SKIP"
        assert "test" in classification.reason.lower()


class TestSuggestionWorkflow:
    """E2E tests for suggestion generation workflow."""

    @pytest.fixture
    def project_state(self, temp_dir):
        """Create project with existing scan state."""
        # Create code state
        code_state = {
            "src/main.py": {
                "hash": "abc123",
                "summary": {
                    "description": "Main entry point",
                    "changes": ["Added new CLI command", "Updated argument parsing"],
                },
                "priority": "HIGH",
                "metadata": {"classification": "HIGH", "magnitude": 0.8},
            },
        }
        (temp_dir / "code-state.json").write_text(json.dumps(code_state))

        # Create doc state
        doc_state = {
            "docs/readme.md": {
                "hash": "def456",
                "summary": {
                    "sections": [
                        {"section_name": "Usage", "summary": "How to use CLI"}
                    ]
                },
            },
        }
        (temp_dir / "doc-state.json").write_text(json.dumps(doc_state))

        return temp_dir, code_state, doc_state

    def test_suggester_generates_from_state(self, project_state, mock_suggester_agent):
        """Test suggester generates suggestions from existing state."""
        from dope.repositories.suggestion_state import SuggestionRepository
        from dope.services.suggester.suggester_service import DocChangeSuggester

        temp_dir, code_state, doc_state = project_state

        repository = SuggestionRepository(temp_dir / "suggestions.json")
        suggester = DocChangeSuggester(
            repository=repository,
            agent=mock_suggester_agent,
        )

        result = suggester.get_suggestions(
            docs_change=doc_state,
            code_change=code_state,
            scope="Python CLI tool for documentation",
        )

        assert isinstance(result, DocSuggestions)
        assert len(result.changes_to_apply) > 0

    def test_suggester_caches_and_reuses(self, project_state, mock_suggester_agent):
        """Test suggester uses cached results when input unchanged."""
        from dope.repositories.suggestion_state import SuggestionRepository
        from dope.services.suggester.suggester_service import DocChangeSuggester

        temp_dir, code_state, doc_state = project_state

        repository = SuggestionRepository(temp_dir / "suggestions.json")
        suggester = DocChangeSuggester(
            repository=repository,
            agent=mock_suggester_agent,
        )

        # First call
        suggester.get_suggestions(
            docs_change=doc_state, code_change=code_state, scope=""
        )
        first_call_count = mock_suggester_agent.run_sync.call_count

        # Second call with same input
        suggester.get_suggestions(
            docs_change=doc_state, code_change=code_state, scope=""
        )
        second_call_count = mock_suggester_agent.run_sync.call_count

        # Should not call agent again
        assert second_call_count == first_call_count


class TestApplyWorkflow:
    """E2E tests for applying suggestions."""

    def test_apply_writes_content(self, temp_dir):
        """Test that apply workflow writes content to files."""
        from dope.cli.apply import _apply_change

        target_path = temp_dir / "docs" / "new_guide.md"
        content = "# New Guide\n\nThis is new documentation."

        _apply_change(target_path, content)

        assert target_path.exists()
        assert target_path.read_text() == content

    def test_apply_creates_directories(self, temp_dir):
        """Test that apply creates nested directories."""
        from dope.cli.apply import _apply_change

        target_path = temp_dir / "deep" / "nested" / "dir" / "file.md"
        content = "Content"

        _apply_change(target_path, content)

        assert target_path.exists()


class TestFullPipeline:
    """Integration test for complete pipeline."""

    @patch("dope.services.describer.strategies.get_doc_summarization_agent")
    @patch("dope.services.describer.strategies.get_code_change_agent")
    def test_scan_to_suggest_pipeline(
        self,
        mock_code_agent_factory,
        mock_doc_agent_factory,
        git_repo_with_changes,
        temp_dir,
        mock_agent,
        mock_suggester_agent,
    ):
        """Test full pipeline from scan to suggestions."""
        repo_path, _ = git_repo_with_changes

        # Configure mock agents
        mock_doc_agent_factory.return_value = mock_agent
        mock_code_agent_factory.return_value = mock_agent

        # Create consumers
        from dope.consumers.doc_consumer import DocConsumer
        from dope.consumers.git_consumer import GitConsumer

        doc_consumer = DocConsumer(
            repo_path / "docs",
            file_type_filter={".md"},
            exclude_dirs=set(),
        )
        git_consumer = GitConsumer(repo_path, "main")

        # Create services
        from dope.repositories.describer_state import DescriberRepository
        from dope.services.describer.describer_base import (
            CodeDescriberService,
            DescriberService,
        )

        doc_repository = DescriberRepository(temp_dir / "doc-state.json")
        doc_service = DescriberService(
            consumer=doc_consumer,
            repository=doc_repository,
        )

        code_repository = DescriberRepository(temp_dir / "code-state.json")
        code_service = CodeDescriberService(
            consumer=git_consumer,
            repository=code_repository,
            enable_filtering=True,
        )

        # Scan docs
        doc_state = doc_service.scan()

        # Scan code
        code_state = code_service.scan()

        # Generate summaries for docs
        for filepath, state_item in list(doc_state.items()):
            if state_item.get("summary") is None and not state_item.get("skipped"):
                doc_state[filepath] = doc_service.describe(filepath, state_item)
        doc_repository.save(doc_state)

        # Generate summaries for code
        for filepath, state_item in list(code_state.items()):
            if state_item.get("summary") is None and not state_item.get("skipped"):
                code_state[filepath] = code_service.describe(filepath, state_item)
        code_repository.save(code_state)

        # Verify state files exist
        assert (temp_dir / "doc-state.json").exists()
        assert (temp_dir / "code-state.json").exists()

        # Now generate suggestions
        from dope.repositories.suggestion_state import SuggestionRepository
        from dope.services.suggester.suggester_service import DocChangeSuggester

        suggestion_repo = SuggestionRepository(temp_dir / "suggestions.json")
        suggester = DocChangeSuggester(
            repository=suggestion_repo,
            agent=mock_suggester_agent,
        )

        suggestions = suggester.get_suggestions(
            docs_change=doc_state,
            code_change=code_state,
            scope="",
        )

        # Verify suggestions were generated
        assert isinstance(suggestions, DocSuggestions)
        assert (temp_dir / "suggestions.json").exists()
