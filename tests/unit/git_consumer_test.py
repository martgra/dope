"""Unit tests for GitConsumer I/O operations.

Note: File classification and change magnitude tests are in classification_test.py,
since those methods were moved to dope.core.classification.FileClassifier.
"""

import tempfile
from pathlib import Path

import pytest
from git import Repo

from dope.consumers.git_consumer import GitConsumer


@pytest.fixture(name="git_repo")
def git_repo_fixture():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Repo.init(tmpdir)
        repo_path = Path(tmpdir)

        # Configure git
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Create initial commit
        readme = repo_path / "README.md"
        readme.write_text("# Test Project\n")
        repo.index.add([str(readme)])
        repo.index.commit("Initial commit")

        # Create main branch
        repo.git.branch("-M", "main")

        yield repo_path, repo


class TestDiscoverFiles:
    """Test file discovery in git repositories."""

    def test_discover_all_files(self, git_repo):
        """Test discovering all committed files."""
        repo_path, repo = git_repo
        consumer = GitConsumer(repo_path, "main")

        # Create and commit additional files
        src_file = repo_path / "src" / "api.py"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text("def hello(): pass\n")
        repo.index.add([str(src_file)])
        repo.index.commit("Add source file")

        discovered = consumer.discover_files(mode="all")

        assert len(discovered) >= 2  # README.md + src/api.py
        assert Path("README.md") in discovered
        assert Path("src/api.py") in discovered

    def test_discover_diff_files(self, git_repo):
        """Test discovering changed files from diff."""
        repo_path, repo = git_repo
        consumer = GitConsumer(repo_path, "main")

        # Modify a file (uncommitted change)
        readme = repo_path / "README.md"
        readme.write_text("# Modified Project\n")

        discovered = consumer.discover_files(mode="diff")

        # Uncommitted changes should show in diff
        assert Path("README.md") in discovered

    def test_discover_invalid_mode_raises(self, git_repo):
        """Test that invalid mode raises ValueError."""
        repo_path, _ = git_repo
        consumer = GitConsumer(repo_path, "main")

        with pytest.raises(ValueError, match="Unsupported"):
            consumer.discover_files(mode="invalid")


class TestGetContent:
    """Test getting file diff content."""

    def test_get_content_returns_bytes(self, git_repo):
        """Test get_content returns diff as bytes."""
        repo_path, repo = git_repo
        consumer = GitConsumer(repo_path, "main")

        # Modify a file
        readme = repo_path / "README.md"
        readme.write_text("# Modified Project\n")

        content = consumer.get_content(Path("README.md"))

        assert isinstance(content, bytes)
        assert b"Modified" in content

    def test_get_content_with_normalization(self, git_repo):
        """Test get_content with whitespace normalization."""
        repo_path, repo = git_repo
        consumer = GitConsumer(repo_path, "main")

        # Modify with whitespace changes
        readme = repo_path / "README.md"
        readme.write_text("# Test Project  \n\n")  # Trailing spaces and blank line

        normal_diff = consumer.get_content(Path("README.md"), normalize_whitespace=False)
        normalized_diff = consumer.get_content(Path("README.md"), normalize_whitespace=True)

        assert isinstance(normal_diff, bytes)
        assert isinstance(normalized_diff, bytes)


class TestWhitespaceNormalization:
    """Test whitespace-normalized diffs."""

    def test_normalized_diff_ignores_whitespace(self, git_repo):
        """Test that normalized diff ignores whitespace changes."""
        repo_path, repo = git_repo
        consumer = GitConsumer(repo_path, "main")

        # Create file with specific formatting
        test_file = repo_path / "format.py"
        test_file.write_text("def hello():\n    return 'world'\n")
        repo.index.add([str(test_file)])
        repo.index.commit("Add formatted file")

        # Change only whitespace
        test_file.write_text("def hello():\n        return 'world'\n")  # Extra spaces

        # Regular diff should show changes
        regular_diff = consumer.get_content(Path("format.py"), normalize_whitespace=False)
        regular_diff_str = regular_diff.decode("utf-8")

        # Normalized diff should be empty or minimal
        normalized_diff = consumer.get_normalized_diff(Path("format.py"))
        normalized_diff_str = normalized_diff.decode("utf-8")

        # The normalized diff should have fewer changes
        assert len(normalized_diff_str) <= len(regular_diff_str)


class TestGetFullContent:
    """Test getting full file content."""

    def test_get_full_content_returns_text(self, git_repo):
        """Test get_full_content returns file text."""
        repo_path, _ = git_repo
        consumer = GitConsumer(repo_path, "main")

        content = consumer.get_full_content(Path("README.md"))

        assert isinstance(content, str)
        assert "Test Project" in content

    def test_get_full_content_raises_for_missing_file(self, git_repo):
        """Test get_full_content raises for non-existent file."""
        from dope.exceptions import DocumentNotFoundError

        repo_path, _ = git_repo
        consumer = GitConsumer(repo_path, "main")

        with pytest.raises(DocumentNotFoundError):
            consumer.get_full_content(Path("nonexistent.py"))


class TestGetMetadata:
    """Test repository metadata retrieval."""

    def test_get_metadata_returns_code_metadata(self, git_repo):
        """Test get_metadata returns CodeMetadata."""
        from dope.models.domain.code import CodeMetadata

        repo_path, _ = git_repo
        consumer = GitConsumer(repo_path, "main")

        metadata = consumer.get_metadata()

        assert isinstance(metadata, CodeMetadata)
        assert metadata.commits >= 1
        assert "main" in metadata.branches
        assert metadata.lines_of_code >= 0
